package app.blackbg

import android.app.Activity
import android.app.WallpaperManager
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.view.WindowInsets
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.Toast

class Preview : Activity() {
    companion object {
        init { System.loadLibrary("blackbg_arm64") }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()

        val root = FrameLayout(this).apply {
            setBackgroundColor(Color.BLACK)
            setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        root.addView(controls, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT,
            FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.CENTER,
        ))
        val choices = mutableListOf<Button>()
        fun addChoice(label: String, icon: Int, action: () -> Unit) {
            val choice = Button(this, null, android.R.attr.borderlessButtonStyle).apply {
                text = label
                isAllCaps = false
                setTextColor(Color.WHITE)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                gravity = Gravity.START or Gravity.CENTER_VERTICAL
                minHeight = dp(56)
                setPaddingRelative(dp(24), dp(8), dp(24), dp(8))
                compoundDrawablePadding = dp(16)
                setCompoundDrawablesRelativeWithIntrinsicBounds(icon, 0, 0, 0)
                setOnClickListener { action() }
            }
            choices.add(choice)
            controls.addView(choice, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT,
            ))
        }

        fun applyWallpaper(flags: Int) {
            choices.forEach { it.isEnabled = false }
            Thread {
                val result = runCatching {
                    val black = Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)
                    black.eraseColor(Color.BLACK)
                    val manager = WallpaperManager.getInstance(this)
                    check(manager.isWallpaperSupported && manager.isSetWallpaperAllowed)
                    check(manager.setBitmap(black, null, false, flags) > 0)
                }
                runOnUiThread {
                    if (!isDestroyed && !isFinishing) {
                        if (result.isSuccess) {
                            setResult(RESULT_OK)
                            finish()
                        } else {
                            Toast.makeText(this, "Couldn’t apply wallpaper.", Toast.LENGTH_LONG).show()
                            choices.forEach { it.isEnabled = true }
                        }
                    }
                }
            }.start()
        }
        addChoice("Lockscreen", R.drawable.ic_lockscreen) { applyWallpaper(WallpaperManager.FLAG_LOCK) }
        addChoice("Homescreen", R.drawable.ic_homescreen) { applyWallpaper(WallpaperManager.FLAG_SYSTEM) }
        addChoice("Both", R.drawable.ic_both) { applyWallpaper(WallpaperManager.FLAG_SYSTEM or WallpaperManager.FLAG_LOCK) }
        addChoice("Cancel", R.drawable.ic_cancel) { finish() }
        setContentView(root)
    }
}
