"use client";

import { useEffect, useRef } from "react";

/**
 * Interactive full-page GLSL shader (shaders.com style).
 * Flowing wave field with a ripple that follows the cursor.
 * Light ACTIA palette (green / teal / blue) so content stays readable.
 */
const FRAG = `
precision highp float;
uniform vec2  u_res;
uniform float u_time;
uniform vec2  u_mouse;   // smoothed cursor, pixels
uniform float u_active;  // 0..1 how "recent" the cursor moved
uniform vec3  u_tone;    // verdict colour — the field drifts toward it

// layered directional swells travelling across the surface
float waveField(vec2 p, float t){
  float s = 0.0;
  s +=       sin(p.x * 2.0 + p.y * 0.6 + t * 1.2);
  s += 0.6 * sin(p.x * 3.4 - p.y * 1.1 + t * 1.7);
  s += 0.5 * sin(p.x * 1.2 + p.y * 2.3 - t * 0.9);
  s += 0.4 * sin((p.x + p.y) * 2.8 + t * 2.1);
  return s;
}

void main(){
  vec2 uv = gl_FragCoord.xy / u_res.xy;
  float aspect = u_res.x / u_res.y;
  vec2 p = (gl_FragCoord.xy - 0.5 * u_res.xy) / u_res.y;
  vec2 m = (u_mouse - 0.5 * u_res.xy) / u_res.y;

  float t = u_time * 0.5;

  // domain warp -> flowing water, not a static grid
  vec2 q = p * 2.2;
  q += 0.35 * vec2(sin(q.y * 1.5 + t), cos(q.x * 1.5 - t * 0.8));

  float w = waveField(q, t);
  float v = 0.5 + 0.16 * w;

  // thin bright crest lines riding the swells
  float crest = smoothstep(0.55, 0.96, sin(w * 1.3 + t));

  // ripple emanating from the cursor, like a stone dropped in water
  float d = length(p - m);
  float ripple = sin(d * 18.0 - u_time * 3.0) * exp(-d * 3.0) * (0.4 + 0.6 * u_active);
  v += ripple * 0.5;
  float glow = exp(-d * 2.2) * (0.3 + 0.5 * u_active);

  vec3 teal   = vec3(0.49, 0.86, 0.74);
  vec3 green  = vec3(0.20, 0.66, 0.33);
  vec3 forest = vec3(0.08, 0.42, 0.22);

  // pull the whole field toward the verdict colour so the background carries it
  teal   = mix(teal,   u_tone + vec3(0.30), 0.55);
  green  = mix(green,  u_tone, 0.60);
  forest = mix(forest, u_tone * 0.65, 0.60);

  vec3 col = mix(teal, green, smoothstep(0.15, 0.85, v));
  col = mix(col, forest, glow * 0.55);
  col += crest * 0.12;                       // foam highlight on the crests

  // keep it airy: blend over a soft off-white, stronger toward edges
  float edge = smoothstep(0.35, 1.1, length(vec2((uv.x-0.5)*aspect, uv.y-0.5)) );
  vec3 bg = vec3(0.965, 0.980, 0.965);
  float alpha = 0.06 + 0.16 * v * (0.35 + edge) + glow * 0.35 + crest * 0.06;

  vec3 outc = mix(bg, col, clamp(alpha, 0.0, 0.5));
  gl_FragColor = vec4(outc, 1.0);
}
`;

const VERT = `
attribute vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

/** Verdict colours, normalised RGB, matching CONVEYOR_TONE in lib/model.js. */
const TONE_RGB = {
  rare: [0.72, 0.52, 0.04],
  common: [0.16, 0.47, 0.84],
  unknown: [0.42, 0.48, 0.44],
};

export default function ShaderBackground({ tone = "unknown" }) {
  const ref = useRef(null);
  const toneRef = useRef(TONE_RGB[tone] || TONE_RGB.unknown);

  /* Keep the live value in a ref so a verdict change never restarts the GL loop. */
  useEffect(() => {
    toneRef.current = TONE_RGB[tone] || TONE_RGB.unknown;
  }, [tone]);

  useEffect(() => {
    const canvas = ref.current;
    const gl = canvas.getContext("webgl", { antialias: true, premultipliedAlpha: false });
    if (!gl) return;

    const compile = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(s));
      }
      return s;
    };
    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "a_pos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(prog, "u_res");
    const uTime = gl.getUniformLocation(prog, "u_time");
    const uMouse = gl.getUniformLocation(prog, "u_mouse");
    const uActive = gl.getUniformLocation(prog, "u_active");
    const uTone = gl.getUniformLocation(prog, "u_tone");
    /* eased so a verdict flip glides rather than snaps */
    const shown = [...toneRef.current];

    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const resize = () => {
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
    };
    resize();
    window.addEventListener("resize", resize);

    const target = { x: canvas.width * 0.7, y: canvas.height * 0.6 };
    const cur = { x: target.x, y: target.y };
    let active = 0;
    const onMove = (e) => {
      target.x = e.clientX * dpr;
      target.y = (window.innerHeight - e.clientY) * dpr; // flip Y for GL
      active = 1;
    };
    window.addEventListener("pointermove", onMove);

    const start = performance.now();
    let raf;
    const loop = (now) => {
      cur.x += (target.x - cur.x) * 0.08;
      cur.y += (target.y - cur.y) * 0.08;
      active *= 0.96;
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, (now - start) / 1000);
      gl.uniform2f(uMouse, cur.x, cur.y);
      gl.uniform1f(uActive, active);
      const want = toneRef.current;
      for (let i = 0; i < 3; i++) shown[i] += (want[i] - shown[i]) * 0.05;
      gl.uniform3f(uTone, shown[0], shown[1], shown[2]);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
    };
  }, []);

  return <canvas ref={ref} className="shader-bg" aria-hidden="true" />;
}
