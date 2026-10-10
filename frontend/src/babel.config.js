module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    // Reanimated 4 / worklets: el plugin debe ir al final. Obligatorio.
    plugins: ['react-native-worklets/plugin'],
  };
};
