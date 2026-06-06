var Clay = require('@rebble/clay');
var clayConfig = require('./config');
var clay = new Clay(clayConfig, null, { autoHandleEvents: false });

Pebble.addEventListener('showConfiguration', function() {
  Pebble.openURL(clay.generateUrl());
});

function valueOf(setting) {
  return typeof setting === 'object' ? setting.value : setting;
}

Pebble.addEventListener('webviewclosed', function(e) {
  if (!e || !e.response) return;

  var settings = clay.getSettings(e.response, false);
  var dict = {};

  if (settings.BG_HEX !== undefined) {
    dict.BG_HEX = valueOf(settings.BG_HEX);
  }
  if (settings.FACE_HEX !== undefined) {
    dict.FACE_HEX = valueOf(settings.FACE_HEX);
  }
  if (settings.HAND_HEX !== undefined) {
    dict.HAND_HEX = valueOf(settings.HAND_HEX);
  }
  if (settings.DIAL_STYLE !== undefined) {
    dict.DIAL_STYLE = parseInt(valueOf(settings.DIAL_STYLE), 10);
  }
  if (settings.FACE_CLEAR !== undefined) {
    dict.FACE_CLEAR = valueOf(settings.FACE_CLEAR) ? 1 : 0;
  }

  Pebble.sendAppMessage(dict);
});
