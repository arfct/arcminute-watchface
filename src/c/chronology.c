#include <pebble.h>
#include "../../build/include/message_keys.auto.h"

// PDC (Pebble Draw Command) structures
typedef struct
{
  int16_t x;
  int16_t y;
} __attribute__((packed)) Point;

typedef struct
{
  uint8_t type;
  uint8_t flags;
  uint8_t stroke_color;
  uint8_t stroke_width;
  uint8_t fill_color;
  uint16_t path_open_radius;
  uint16_t num_points;
  Point points[];
} __attribute__((packed)) PebbleDrawCommand;

typedef struct
{
  uint16_t num_commands;
  PebbleDrawCommand commands[];
} __attribute__((packed)) PebbleDrawCommandList;

typedef struct
{
  uint16_t width;
  uint16_t height;
} __attribute__((packed)) ViewBox;

typedef struct
{
  uint8_t version;
  uint8_t reserved;
  ViewBox view_box;
  PebbleDrawCommandList command_list;
} __attribute__((packed)) PebbleDrawCommandImage;

typedef struct
{
  char magic[4];
  uint32_t image_size;
  PebbleDrawCommandImage image;
} __attribute__((packed)) PebbleDrawCommandImageFile;

// Function to create a simple PDC image in memory
PebbleDrawCommandImageFile *create_pdc_image(uint16_t width, uint16_t height, uint16_t num_commands)
{
  size_t total_size = sizeof(PebbleDrawCommandImageFile) + (num_commands * sizeof(PebbleDrawCommand));
  PebbleDrawCommandImageFile *pdc = malloc(total_size);
  if (!pdc)
    return NULL;

  memcpy(pdc->magic, "PDCI", 4);
  pdc->image_size = total_size - 8;
  pdc->image.version = 1;
  pdc->image.reserved = 0;
  pdc->image.view_box.width = width;
  pdc->image.view_box.height = height;
  pdc->image.command_list.num_commands = num_commands;

  return pdc;
}

// Function to add points to a PDC draw command
bool add_points_to_command(PebbleDrawCommand *command, const Point *points, uint16_t num_points)
{
  if (!command || !points || num_points == 0)
    return false;

  command->num_points = num_points;
  memcpy(command->points, points, num_points * sizeof(Point));

  return true;
}

static Window *s_main_window;
static Layer *s_face_layer;
static Layer *s_hand_layer;
static TextLayer *s_battery_layer;
static bool debug = false;
static float s_scale = 1.0f;
static float s_mark_scale = 1.0f;
static float s_stroke_scale = 1.0f;
static int16_t s_orbit_inset = 150;
static GColor s_background_color;
static GColor s_face_color;
static GColor s_hand_color;
static bool s_face_clear = true;
static int s_dial_style = 0;
static GFont s_large_numeral_font;

static GColor background_color() {
  return s_background_color;
}

// Scale a gabbro-reference stroke/dot width down for smaller screens, never below 1px.
static uint8_t scaled_stroke(int16_t gabbro_px) {
  int16_t w = (int16_t)(gabbro_px * s_stroke_scale + 0.5f);
  return w < 1 ? 1 : (uint8_t)w;
}

static GColor face_color() {
  return s_face_clear ? s_background_color : s_face_color;
}

static bool color_is_light(GColor c) {
#if defined(PBL_COLOR)
  return ((int)c.r + (int)c.g + (int)c.b) >= 5;
#else
  return gcolor_equal(c, GColorWhite);
#endif
}

static bool face_is_light() {
  return color_is_light(face_color());
}

static GColor face_text_color() {
  return face_is_light() ? GColorBlack : GColorWhite;
}

static GColor face_minor_tick_color() {
  return face_is_light() ? GColorDarkGray : GColorLightGray;
}

static GColor hand_color() {
#if defined(PBL_COLOR)
  return s_hand_color;
#else
  return face_is_light() ? GColorBlack : GColorWhite;
#endif
}
// static int font_size_index = 1; // 0=large, 1=medium, 2=small, 3=xsmall (commented out)

static void inbox_received_callback(DictionaryIterator *iterator, void *context);
static void inbox_dropped_callback(AppMessageResult reason, void *context);
static void outbox_failed_callback(DictionaryIterator *iterator, AppMessageResult reason, void *context);
static void outbox_sent_callback(DictionaryIterator *iterator, void *context);
// Font size setting commented out - not working correctly
// static GFont get_font_for_index(int index);

// static GFont get_font_for_index(int index)
// {
//   switch (index)
//   {
//   case 0:
//     return fonts_get_system_font(FONT_KEY_BITHAM_34_MEDIUM_NUMBERS);
//   case 1:
//     return fonts_get_system_font(FONT_KEY_GOTHIC_28_BOLD);
//   case 2:
//     return fonts_get_system_font(FONT_KEY_GOTHIC_24_BOLD);
//   case 3:
//     return fonts_get_system_font(FONT_KEY_GOTHIC_18_BOLD);
//   default:
//     return fonts_get_system_font(FONT_KEY_GOTHIC_28_BOLD);
//   }
// }

static void update_time()
{
  // Get a tm structure
  time_t temp = time(NULL);
  struct tm *tick_time = localtime(&temp);

  // Write the current hours and minutes into a buffer
  static char s_buffer[8];
  strftime(s_buffer, sizeof(s_buffer), clock_is_24h_style() ? "%H:%M" : "%I:%M", tick_time);
}
static void battery_handler(BatteryChargeState charge_state)
{
  static char s_battery_buffer[16];

  if (charge_state.is_charging)
  {
    snprintf(s_battery_buffer, sizeof(s_battery_buffer), "%d", charge_state.charge_percent);
  }
  else
  {
    snprintf(s_battery_buffer, sizeof(s_battery_buffer), "%d", charge_state.charge_percent);
  }
  text_layer_set_text(s_battery_layer, s_battery_buffer);
}

static void update_frame_location()
{
  time_t temp = time(NULL);
  struct tm *tick_time = localtime(&temp);
  int bhour = tick_time->tm_hour;
  int bmin = tick_time->tm_min;
  float angle = 30 * ((float)(bhour % 12) + ((float)bmin / 60));
  if (debug)
    angle = 12 * tick_time->tm_sec;

  GRect frame = layer_get_frame(s_face_layer);
  GRect frame2 = layer_get_frame(s_hand_layer);

  GPoint origin = gpoint_from_polar(grect_inset(frame2, GEdgeInsets(-s_orbit_inset)), GOvalScaleModeFitCircle, DEG_TO_TRIGANGLE(angle + 180));
  frame.origin = origin;
  frame.origin.x -= frame.size.w / 2;
  frame.origin.y -= frame.size.h / 2;

  layer_set_frame(s_face_layer, frame);
}

static void tick_handler(struct tm *tick_time, TimeUnits units_changed)
{
  update_time();
  layer_mark_dirty(s_hand_layer);
  update_frame_location();
}

static void my_hand_draw(Layer *layer, GContext *ctx)
{
  // GRect bounds = layer_get_bounds(layer);
  GRect face_frame = layer_get_frame(s_face_layer);

  time_t temp = time(NULL);
  struct tm *tick_time = localtime(&temp);
  int bhour = tick_time->tm_hour;
  int bmin = tick_time->tm_min;

  float angle = 30 * ((float)(bhour % 12) + ((float)bmin / 60));
  if (debug)
    angle = 12 * tick_time->tm_sec;

  GPoint center = GPoint(face_frame.origin.x + face_frame.size.w / 2, face_frame.origin.y + face_frame.size.h / 2);
  GPoint end_point = gpoint_from_polar(face_frame, GOvalScaleModeFitCircle, DEG_TO_TRIGANGLE(angle));

  uint8_t stroke_width =
#if PBL_DISPLAY_WIDTH == 260
      9;
#elif PBL_DISPLAY_WIDTH == 200
      6;
#else
      5;
#endif

  graphics_context_set_stroke_color(ctx, hand_color());
  graphics_context_set_stroke_width(ctx, stroke_width);
  graphics_draw_line(ctx, center, end_point);
}

static void my_face_draw(Layer *layer, GContext *ctx)
{
  GRect bounds = layer_get_bounds(layer);
  const int16_t half_h = bounds.size.h / 2;
  const bool large_numerals = s_dial_style == 1;
  const int16_t hour_inset = large_numerals
      ? (int16_t)(40 * s_mark_scale)
      : (int16_t)(20 * s_scale);
  const int16_t ascender = large_numerals
#if PBL_DISPLAY_WIDTH >= 200
      ? 24
#else
      ? 17
#endif
      : (int16_t)(8 * s_scale);

  graphics_context_set_antialiased(ctx, false);

  // Fill the face disk (omitted when face is transparent), 4px beyond the marker ring
  if (!s_face_clear) {
    graphics_context_set_fill_color(ctx, face_color());
    graphics_fill_circle(ctx, GPoint(half_h, half_h), bounds.size.w / 2 + 8);
  }

  graphics_context_set_stroke_color(ctx, face_text_color());
  graphics_context_set_stroke_width(ctx, 2);
  graphics_context_set_text_color(ctx, face_text_color());

  for (int i = 0; i < 12; i++)
  {
    int angle = DEG_TO_TRIGANGLE(i * 30);

    static char buf[] = "000";
    snprintf(buf, sizeof(buf), "%01d", i == 0 ? 12 : i);
    GFont number_font = large_numerals
        ? s_large_numeral_font
        : fonts_get_system_font(
#if PBL_DISPLAY_WIDTH == 260
              FONT_KEY_BITHAM_42_LIGHT
#else
              FONT_KEY_BITHAM_34_MEDIUM_NUMBERS
#endif
          );
    GRect meas_rect = GRect(0, 0, bounds.size.w, bounds.size.h);
    GSize size = graphics_text_layout_get_content_size(buf, number_font, meas_rect,
                                                       GTextOverflowModeFill, GTextAlignmentCenter);

    // Font metric dead-space above the visual digit area
    const int16_t box_top_offset = large_numerals ? (size.h * 27 / 100) : ascender;
    const int16_t box_h = size.h - box_top_offset;

    // Radial unit vector (outward from center, toward tick)
    int32_t rdx = sin_lookup(angle);
    int32_t rdy = -cos_lookup(angle);
    int32_t abs_rdx = rdx < 0 ? -rdx : rdx;
    int32_t abs_rdy = rdy < 0 ? -rdy : rdy;

    // Distance from box center to nearest box edge along the radial direction
    int32_t hw = size.w / 2;
    int32_t hh = box_h / 2;
    int32_t t_x = abs_rdx > 0 ? (hw * TRIG_MAX_RATIO / abs_rdx) : INT16_MAX;
    int32_t t_y = abs_rdy > 0 ? (hh * TRIG_MAX_RATIO / abs_rdy) : INT16_MAX;
    int32_t d_edge = t_x < t_y ? t_x : t_y;

    const int16_t gap = hour_inset / 2;
    GPoint tick_inner = gpoint_from_polar(grect_crop(bounds, hour_inset), GOvalScaleModeFitCircle, angle);
    GPoint box_center = GPoint(
        tick_inner.x - (int16_t)((gap + d_edge) * rdx / TRIG_MAX_RATIO),
        tick_inner.y - (int16_t)((gap + d_edge) * rdy / TRIG_MAX_RATIO));

    GRect text_rect = GRect(
        box_center.x - size.w / 2,
        box_center.y - box_h / 2 - box_top_offset,
        size.w, size.h);

    graphics_draw_text(ctx, buf, number_font,
#if PBL_DISPLAY_WIDTH == 260
                       text_rect,
#else
                       large_numerals ? text_rect : grect_inset(text_rect, GEdgeInsets4(-8, 0, 0, 0)),
#endif
                       GTextOverflowModeFill, GTextAlignmentCenter, NULL);

#ifdef DEBUG_BOXES
    graphics_context_set_stroke_width(ctx, 1);
    graphics_draw_rect(ctx, GRect(box_center.x - size.w / 2, box_center.y - box_h / 2, size.w, box_h));
#endif

    graphics_context_set_stroke_color(ctx, face_text_color());
    graphics_context_set_stroke_width(ctx, large_numerals ? scaled_stroke(6)
#if PBL_DISPLAY_WIDTH == 260
                                                          : 3);
#else
                                                          : 2);
#endif
    graphics_draw_line(ctx,
                       gpoint_from_polar(grect_crop(bounds, hour_inset), GOvalScaleModeFitCircle, angle),
                       gpoint_from_polar(bounds, GOvalScaleModeFitCircle, angle));

    for (int j = 1; j < 12; j++)
    {
      int16_t line_length;
      GColor line_color = face_minor_tick_color();

      angle += DEG_TO_TRIGANGLE(2.5);
      graphics_context_set_stroke_color(ctx, line_color);
      if (j % 3 == 0) {
        graphics_context_set_stroke_width(ctx, large_numerals ? scaled_stroke(4) : 2);
        graphics_draw_line(ctx,
                           gpoint_from_polar(grect_crop(bounds, hour_inset / 2), GOvalScaleModeFitCircle, angle),
                           gpoint_from_polar(bounds, GOvalScaleModeFitCircle, angle));
      } else {
        graphics_context_set_fill_color(ctx, line_color);
        GPoint dot = gpoint_from_polar(bounds, GOvalScaleModeFitCircle, angle);
        graphics_fill_circle(ctx, dot, large_numerals ? scaled_stroke(3) : 2);
      }
    }
  }
}

static void main_window_load(Window *window)
{
  Layer *window_layer = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(window_layer);

  int16_t screen_size = bounds.size.w < bounds.size.h ? bounds.size.w : bounds.size.h;
  s_scale = 180.0f / (float)screen_size;
  // Marks and stroke widths scale proportionally with the screen; gabbro (260px) is the reference platform.
  s_mark_scale = 180.0f * (float)screen_size / (260.0f * 260.0f);
  s_stroke_scale = (float)screen_size / 260.0f;
  s_orbit_inset = (int16_t)(PBL_IF_ROUND_ELSE(130.0f, 150.0f) * (float)screen_size / 180.0f);

  s_face_layer = layer_create(GRect(0, 0, bounds.size.h * 3, bounds.size.h * 3));
  layer_set_update_proc(s_face_layer, my_face_draw);
  layer_set_clips(s_face_layer, false);

  s_hand_layer = layer_create(bounds);
  layer_set_update_proc(s_hand_layer, my_hand_draw);

  // Create the TextLayer with specific bounds
  s_battery_layer = text_layer_create(
      GRect(0, PBL_IF_ROUND_ELSE(58, 52), bounds.size.w, 50));

  // Improve the layout to be more like a watchface
  // text_layer_set_background_color(s_battery_layer, GColorClear);
  // text_layer_set_text_color(s_battery_layer, GColorDarkGray);
  // text_layer_set_text(s_battery_layer, "50");
  // text_layer_set_font(s_battery_layer, fonts_get_system_font(FONT_KEY_GOTHIC_28_BOLD));
  // text_layer_set_text_alignment(s_battery_layer, GTextAlignmentCenter);

  update_frame_location();

  // Face below, hand on top so the hand renders over the dial and marks
  layer_add_child(window_layer, s_face_layer);
  layer_add_child(window_layer, s_hand_layer);
}

static void inbox_received_callback(DictionaryIterator *iterator, void *context)
{
  Tuple *bg_tuple = dict_find(iterator, MESSAGE_KEY_BG_HEX);
  if (bg_tuple)
  {
    int32_t hex = bg_tuple->value->int32;
    s_background_color = GColorFromHEX(hex);
    persist_write_int(5, hex);
  }

  Tuple *face_hex_tuple = dict_find(iterator, MESSAGE_KEY_FACE_HEX);
  if (face_hex_tuple)
  {
    int32_t hex = face_hex_tuple->value->int32;
    s_face_color = GColorFromHEX(hex);
    persist_write_int(6, hex);
  }

  Tuple *hand_hex_tuple = dict_find(iterator, MESSAGE_KEY_HAND_HEX);
  if (hand_hex_tuple)
  {
    int32_t hex = hand_hex_tuple->value->int32;
    s_hand_color = GColorFromHEX(hex);
    persist_write_int(7, hex);
  }

  Tuple *dial_style_tuple = dict_find(iterator, MESSAGE_KEY_DIAL_STYLE);
  if (dial_style_tuple)
  {
    s_dial_style = dial_style_tuple->value->int32;
    persist_write_int(9, s_dial_style);
  }

  Tuple *face_clear_tuple = dict_find(iterator, MESSAGE_KEY_FACE_CLEAR);
  if (face_clear_tuple)
  {
    s_face_clear = face_clear_tuple->value->int32 != 0;
    persist_write_bool(8, s_face_clear);
  }

  window_set_background_color(s_main_window, background_color());
  layer_mark_dirty(s_face_layer);
  layer_mark_dirty(s_hand_layer);

  // Font size setting commented out - not working correctly
  // Tuple *font_size_tuple = dict_find(iterator, MESSAGE_KEY_FONT_SIZE);
  // if (font_size_tuple)
  // {
  //   font_size_index = font_size_tuple->value->int32;
  //   if (font_size_index < 0 || font_size_index > 3)
  //   {
  //     font_size_index = 1; // default to medium
  //   }
  //   persist_write_int(1, font_size_index);
  //   APP_LOG(APP_LOG_LEVEL_INFO, "Font size changed to index: %d", font_size_index);
  //   layer_mark_dirty(s_face_layer);
  // }
}

static void inbox_dropped_callback(AppMessageResult reason, void *context)
{
  APP_LOG(APP_LOG_LEVEL_ERROR, "Message dropped!");
}

static void outbox_failed_callback(DictionaryIterator *iterator, AppMessageResult reason, void *context)
{
  APP_LOG(APP_LOG_LEVEL_ERROR, "Outbox send failed!");
}

static void outbox_sent_callback(DictionaryIterator *iterator, void *context)
{
  APP_LOG(APP_LOG_LEVEL_INFO, "Outbox send success!");
}

static void main_window_unload(Window *window)
{
  // Destroy TextLayer
  layer_destroy(s_face_layer);
}

static void init()
{
  s_background_color = GColorFromHEX(persist_exists(5) ? persist_read_int(5) : 0x000000);
  s_face_color = GColorFromHEX(persist_exists(6) ? persist_read_int(6) : 0x000000);
  s_hand_color = GColorFromHEX(persist_exists(7) ? persist_read_int(7) : 0xFF0000);
  s_face_clear = persist_exists(8) ? persist_read_bool(8) : true;
  s_dial_style = persist_exists(9) ? persist_read_int(9) : 0;

  s_large_numeral_font = fonts_load_custom_font(resource_get_handle(
#if PBL_DISPLAY_WIDTH >= 200
      RESOURCE_ID_FONT_HELVETICA_95
#else
      RESOURCE_ID_FONT_HELVETICA_67
#endif
      ));
  // font_size_index = persist_exists(1) ? persist_read_int(1) : 1; // default to medium (commented out)

  // Create main Window element and assign to pointer
  s_main_window = window_create();
  window_set_background_color(s_main_window, background_color());

  // Set handlers to manage the elements inside the Window
  window_set_window_handlers(s_main_window, (WindowHandlers){
                                                .load = main_window_load,
                                                .unload = main_window_unload});

  // Show the Window on the watch, with animated=true
  window_stack_push(s_main_window, true);

  // Make sure the time is displayed from the start
  update_time();

  // Register with TickTimerService
  tick_timer_service_subscribe(SECOND_UNIT, tick_handler);
  battery_state_service_subscribe(battery_handler);

  // Register callbacks for AppMessage
  app_message_register_inbox_received(inbox_received_callback);
  app_message_register_inbox_dropped(inbox_dropped_callback);
  app_message_register_outbox_failed(outbox_failed_callback);
  app_message_register_outbox_sent(outbox_sent_callback);

  // Open AppMessage with reasonable buffer sizes
  app_message_open(app_message_inbox_size_maximum(), app_message_outbox_size_maximum());
}

static void deinit()
{
  fonts_unload_custom_font(s_large_numeral_font);
  window_destroy(s_main_window);
}

int main(void)
{
  init();
  app_event_loop();
  deinit();
}