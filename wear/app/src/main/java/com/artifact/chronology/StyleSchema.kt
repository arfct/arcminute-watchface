package com.artifact.chronology

import android.content.Context
import androidx.wear.watchface.style.UserStyleSchema
import androidx.wear.watchface.style.UserStyleSetting
import androidx.wear.watchface.style.UserStyleSetting.BooleanUserStyleSetting
import androidx.wear.watchface.style.UserStyleSetting.ListUserStyleSetting
import androidx.wear.watchface.style.WatchFaceLayer

/**
 * User style schema mirroring the Pebble Clay config: dial style, background,
 * transparent face, face color, and hand color.
 */
object StyleSchema {
    const val ID_DIAL_STYLE = "dial_style"
    const val ID_BG_COLOR = "bg_color"
    const val ID_FACE_CLEAR = "face_clear"
    const val ID_FACE_COLOR = "face_color"
    const val ID_HAND_COLOR = "hand_color"

    const val OPTION_CLASSIC = "classic"
    const val OPTION_LARGE = "large"

    @Suppress("DEPRECATION")
    private fun colorOption(context: Context, id: String, nameRes: Int): ListUserStyleSetting.ListOption {
        val name = context.getString(nameRes)
        return ListUserStyleSetting.ListOption(
            UserStyleSetting.Option.Id(id), name, name, icon = null
        )
    }

    @Suppress("DEPRECATION")
    fun create(context: Context): UserStyleSchema {
        val layers = listOf(WatchFaceLayer.BASE)

        val dialStyle = ListUserStyleSetting(
            UserStyleSetting.Id(ID_DIAL_STYLE),
            context.getString(R.string.setting_dial_style),
            context.getString(R.string.setting_dial_style_desc),
            icon = null,
            options = listOf(
                colorOption(context, OPTION_LARGE, R.string.style_large),
                colorOption(context, OPTION_CLASSIC, R.string.style_classic)
            ),
            layers
        )

        val bgColor = ListUserStyleSetting(
            UserStyleSetting.Id(ID_BG_COLOR),
            context.getString(R.string.setting_bg_color),
            context.getString(R.string.setting_bg_color_desc),
            icon = null,
            options = listOf(
                colorOption(context, "black", R.string.color_black),
                colorOption(context, "white", R.string.color_white),
                colorOption(context, "blue", R.string.color_blue),
                colorOption(context, "green", R.string.color_green)
            ),
            layers
        )

        val faceClear = BooleanUserStyleSetting(
            UserStyleSetting.Id(ID_FACE_CLEAR),
            context.getString(R.string.setting_face_clear),
            context.getString(R.string.setting_face_clear_desc),
            icon = null,
            layers,
            defaultValue = true
        )

        val faceColor = ListUserStyleSetting(
            UserStyleSetting.Id(ID_FACE_COLOR),
            context.getString(R.string.setting_face_color),
            context.getString(R.string.setting_face_color_desc),
            icon = null,
            options = listOf(
                colorOption(context, "black", R.string.color_black),
                colorOption(context, "white", R.string.color_white),
                colorOption(context, "gray", R.string.color_gray)
            ),
            layers
        )

        val handColor = ListUserStyleSetting(
            UserStyleSetting.Id(ID_HAND_COLOR),
            context.getString(R.string.setting_hand_color),
            context.getString(R.string.setting_hand_color_desc),
            icon = null,
            options = listOf(
                colorOption(context, "red", R.string.color_red),
                colorOption(context, "white", R.string.color_white),
                colorOption(context, "black", R.string.color_black),
                colorOption(context, "yellow", R.string.color_yellow),
                colorOption(context, "blue", R.string.color_blue)
            ),
            layers
        )

        return UserStyleSchema(listOf(dialStyle, bgColor, faceClear, faceColor, handColor))
    }
}
