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

float wave(vec2 p, float t){
  float w = 0.0;
  w += sin(p.x * 3.0 + t * 1.3);
  w += sin(p.y * 4.0 - t * 1.1);
  w += sin((p.x + p.y) * 2.5 + t * 0.9);
  w += sin(length(p) * 5.0 - t * 1.6);
  return w * 0.25;
}

void main(){
  vec2 uv = gl_FragCoord.xy / u_res.xy;
  float aspect = u_res.x / u_res.y;
  vec2 p = (gl_FragCoord.xy - 0.5 * u_res.xy) / u_res.y;
  vec2 m = (u_mouse - 0.5 * u_res.xy) / u_res.y;

  float t = u_time * 0.35;

  // domain warp for organic flow
  vec2 q = p;
  q += 0.18 * vec2(sin(p.y * 3.0 + t), cos(p.x * 3.0 - t));

  // ripple emanating from the cursor
  float d = length(p - m);
  float ripple = sin(d * 16.0 - u_time * 2.6) * exp(-d * 2.6) * (0.5 + 0.5 * u_active);

  float v = 0.5 + wave(q, t) + ripple * 0.6;
  v = clamp(v, 0.0, 1.0);

  float glow = exp(-d * 2.0) * (0.35 + 0.45 * u_active);

  // halftone-dot shimmer (nod to the reference art), very subtle
  vec2 gp = fract(gl_FragCoord.xy / 22.0) - 0.5;
  float dots = smoothstep(0.36, 0.30, length(gp)) * (0.06 + 0.10 * v);

  vec3 teal  = vec3(0.56, 0.91, 0.82);
  vec3 green = vec3(0.11, 0.70, 0.36);
  vec3 blue  = vec3(0.16, 0.42, 1.00);

  vec3 col = mix(teal, green, smoothstep(0.15, 0.85, v));
  col = mix(col, blue, glow * 0.7);

  // keep it airy: blend over a soft off-white, stronger toward edges
  float edge = smoothstep(0.35, 1.1, length(vec2((uv.x-0.5)*aspect, uv.y-0.5)) );
  vec3 bg = vec3(0.965, 0.980, 0.965);
  float alpha = 0.06 + 0.14 * v * (0.35 + edge) + glow * 0.35 + dots;

  vec3 outc = mix(bg, col, clamp(alpha, 0.0, 0.55));
  gl_FragColor = vec4(outc, 1.0);
}
`;

const VERT = `
attribute vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

export default function ShaderBackground() {
  const ref = useRef(null);

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
