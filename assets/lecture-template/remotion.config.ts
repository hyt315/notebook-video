import {Config} from '@remotion/cli/config';

const stripSourceMapUrls = {
  apply(compiler: any) {
    compiler.hooks.thisCompilation.tap('StripSourceMapUrl', (compilation: any) => {
      // Stage 5000 (PROCESS_ASSETS_STAGE_REPORT) runs after all assets & devtool transforms finish.
      compilation.hooks.processAssets.tap(
        {name: 'StripSourceMapUrl', stage: 5000},
        (assets: Record<string, any>) => {
          for (const [name, asset] of Object.entries(assets)) {
            if (!name.endsWith('.js')) continue;
            const raw = String(asset.source());
            if (!raw.includes('sourceMappingURL=')) continue;
            const cleaned = raw.replace(/^[ \t]*\/\/[#@]\s*sourceMappingURL=[^\r\n]*$/gm, '');
            if (cleaned.length === raw.length) continue;
            const buf = Buffer.from(cleaned, 'utf8');
            compilation.updateAsset(name, {
              source: () => cleaned,
              buffer: () => buf,
              size: () => buf.length,
            });
          }
        },
      );
    });
  },
};

Config.overrideWebpackConfig((currentConfiguration) => {
  return {
    ...currentConfiguration,
    devtool: false,
    plugins: [...(currentConfiguration.plugins ?? []), stripSourceMapUrls],
  };
});
