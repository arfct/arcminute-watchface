package com.artifact.chronology.editor

import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import androidx.wear.watchface.editor.EditorSession
import androidx.wear.watchface.style.UserStyleSetting
import androidx.wear.watchface.style.UserStyleSetting.BooleanUserStyleSetting
import androidx.wear.watchface.style.UserStyleSetting.ListUserStyleSetting
import kotlinx.coroutines.launch

/**
 * Minimal on-watch style editor: one button per setting, tap to cycle
 * through its options. EditorSession commits the style when the activity
 * finishes.
 */
class EditorActivity : ComponentActivity() {

    private lateinit var session: EditorSession

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            try {
                session = EditorSession.createOnWatchEditorSession(this@EditorActivity)
            } catch (e: Exception) {
                // Launched without the EditorRequest extras the system supplies
                finish()
                return@launch
            }
            buildUi()
        }
    }

    private fun buildUi() {
        val density = resources.displayMetrics.density
        val pad = (24 * density).toInt()
        val list = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(pad, pad * 2, pad, pad * 2)
        }

        for (setting in session.userStyleSchema.userStyleSettings) {
            val button = Button(this)
            fun refresh() {
                button.text = "${setting.displayName}\n${optionLabel(currentOption(setting))}"
            }
            button.setOnClickListener {
                cycleOption(setting)
                refresh()
            }
            refresh()
            list.addView(button)
        }

        setContentView(ScrollView(this).apply { addView(list) })
    }

    private fun currentOption(setting: UserStyleSetting): UserStyleSetting.Option =
        session.userStyle.value[setting] ?: setting.defaultOption

    private fun cycleOption(setting: UserStyleSetting) {
        val options = setting.options
        val currentId = currentOption(setting).id
        val index = options.indexOfFirst { it.id == currentId }
        val next = options[(index + 1) % options.size]
        val mutable = session.userStyle.value.toMutableUserStyle()
        mutable[setting] = next
        session.userStyle.value = mutable.toUserStyle()
    }

    private fun optionLabel(option: UserStyleSetting.Option): CharSequence = when (option) {
        is ListUserStyleSetting.ListOption -> option.displayName
        is BooleanUserStyleSetting.BooleanOption -> if (option.value) "On" else "Off"
        else -> String(option.id.value)
    }
}
