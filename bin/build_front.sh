echo "Installing pnpm dependencies."
pnpm install --frozen-lockfile --dev --ignore-scripts
echo "Building front."
pnpm run build
pnpm prune --production