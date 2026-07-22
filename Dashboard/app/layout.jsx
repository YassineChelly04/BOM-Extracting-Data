import "./globals.css";

export const metadata = {
  title: "ACTIA · Material Composition Dashboard",
  description: "BOM material composition report — generated from materials_summary.csv",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
