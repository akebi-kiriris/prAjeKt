/**
 * Stryker configuration for prajekt frontend mutation testing
 * Targets: src/utils (formatters, validators, payloadMappers)
 */
const config = {
  packageManager: 'npm',
  reporters: ['html', 'clear-text'],
  testRunner: 'vitest',
  coverageAnalysis: 'perTest',
  mutate: [
    'src/utils/**/*.ts',
    '!src/utils/**/*.test.ts',
    '!src/utils/**/__tests__/**',
  ],
  vitest: {
    configFile: 'vitest.config.ts',
  },
  concurrency: 2,
  maxTestRunnerReuse: 1,
  timeoutMS: 60000,
};

export default config;
