import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata={title:"CertiChain | Certificate Verification",description:"AI-assisted blockchain certificate verification"};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
