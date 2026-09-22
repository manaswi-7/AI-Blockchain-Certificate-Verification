/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ["onnxruntime-node", "sharp"],
  outputFileTracingIncludes: {
    "/api/verify/upload": [
      "./models/**/*",
      "./frontend/models/**/*",
    ],
  },
};

export default nextConfig;
