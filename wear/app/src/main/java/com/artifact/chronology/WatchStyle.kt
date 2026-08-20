package com.artifact.chronology

import android.graphics.Color
import androidx.wear.watchface.style.UserStyle
import androidx.wear.watchface.style.UserStyleSetting

/** Resolved style values used by the renderer. Defaults match the Pebble defaults. */
data class WatchStyle(
    val bgColor: Int = Color.BLACK,
    val faceColor: Int = Color.BLACK,
    val handColor: Int = COLOR_RED,
    val faceClear: Boolean = true,
    val largeNumerals: Boolean = true
) {
    companion object {
        const val COLOR_RED = 0xFFFF0000.toInt()

        private val COLORS = mapOf(
            "black" to Color.BLACK,
            "white" to Color.WHITE,
            "gray" to 0xFFAAAAAA.toInt(),
            "blue" to 0xFF0000FF.toInt(),
            "green" to 0xFF00AA00.toInt(),
            "red" to COLOR_RED,
            "yellow" to 0xFFFFFF00.toInt()
        )

        fun fromUserStyle(userStyle: UserStyle): WatchStyle {
            var style = WatchStyle()
            for ((setting, option) in userStyle) {
                val optionId = String(option.id.value)
                when (setting.id.value) {
                    StyleSchema.ID_DIAL_STYLE ->
                        style = style.copy(largeNumerals = optionId == StyleSchema.OPTION_LARGE)
                    StyleSchema.ID_BG_COLOR ->
                        style = style.copy(bgColor = COLORS[optionId] ?: Color.BLACK)
                    StyleSchema.ID_FACE_COLOR ->
                        style = style.copy(faceColor = COLORS[optionId] ?: Color.BLACK)
                    StyleSchema.ID_HAND_COLOR ->
                        style = style.copy(handColor = COLORS[optionId] ?: COLOR_RED)
                    StyleSchema.ID_FACE_CLEAR -> {
                        val on = (option as? UserStyleSetting.BooleanUserStyleSetting.BooleanOption)
                            ?.value ?: true
                        style = style.copy(faceClear = on)
                    }
                }
            }
            return style
        }
    }
}
