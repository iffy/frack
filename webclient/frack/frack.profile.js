var profile = {
  basePath: '..',
  action: 'release',
  cssOptimize: 'comments',
  mini: true,
  optimize: 'closure',
  layerOptimize: 'closure',
  'stripConsole': true,
  'selectorEngine': 'lite',
  layers: {
    'dojo/dojo': {
      include: ['dojo/dojo', 'frack/main', 'frack/run'],
      boot: true,
      customBase: true
    }
  },
  resourceTags: {
    test: function (filename, mid) {
      return /test_.*\.js$/.test(filename);
    },
    amd: function (filename, mid) {
      return /\.js$/.test(filename);
    },
    miniExclude: function (filename, mid) {
      return mid in {
        'frack/profile': 1
      };
    }
  }
};