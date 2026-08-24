module.exports = [
  {
    "type": "heading",
    "defaultValue": "Chronology Configuration"
  },
  {
    "type": "section",
    "items": [
      {
        "type": "heading",
        "defaultValue": "Display Settings"
      },
      {
        "type": "select",
        "messageKey": "DIAL_STYLE",
        "label": "Dial style",
        "defaultValue": 1,
        "options": [
          { "label": "Classic", "value": 0 },
          { "label": "Large numerals", "value": 1 }
        ]
      },
      {
        "type": "color",
        "messageKey": "BG_HEX",
        "label": "Background color",
        "defaultValue": "0x000000",
        "sunlight": true
      },
      {
        "type": "toggle",
        "messageKey": "FACE_CLEAR",
        "label": "Transparent face",
        "description": "When on, the face uses the background color.",
        "defaultValue": true
      },
      {
        "type": "color",
        "messageKey": "FACE_HEX",
        "label": "Face color",
        "defaultValue": "0x000000",
        "sunlight": true
      },
      {
        "type": "color",
        "messageKey": "HAND_HEX",
        "label": "Hand color",
        "defaultValue": "0xFF0000",
        "sunlight": true
      },
      {
        "type": "toggle",
        "messageKey": "THICK_HAND",
        "label": "Thick hand",
        "description": "Draws the hand one pixel wider.",
        "defaultValue": false
      }
    ]
  },
  {
    "type": "submit",
    "defaultValue": "Save Settings"
  }
];
