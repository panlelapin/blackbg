package app.blackbg

import android.app.Activity
import android.app.WallpaperManager
import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.WindowInsets
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.window.OnBackInvokedDispatcher

private enum class Status { Ready, Writing, Applied, Failed }

// State/observer changes are serialized on the main thread. The worker owns no Activity.
private class ApplyOperation {
    var status = Status.Ready
        private set
    var observer: (() -> Unit)? = null

    fun start(context: Context, flags: Int) {
        if (status == Status.Writing || status == Status.Applied) return
        status = Status.Writing
        observer?.invoke()
        Thread {
            val outcome = try {
                val manager = WallpaperManager.getInstance(context)
                check(manager.isWallpaperSupported && manager.isSetWallpaperAllowed)
                context.resources.openRawResource(R.raw.black).use {
                    check(manager.setStream(it, null, false, flags) > 0)
                }
                Status.Applied
            } catch (_: Exception) {
                Status.Failed
            }
            Handler(Looper.getMainLooper()).post {
                status = outcome
                observer?.invoke()
            }
        }.start()
    }
}

class Preview : Activity() {
    companion object {
        init { System.loadLibrary("blackbg_arm64") }
    }

    private lateinit var operation: ApplyOperation
    private val choices = mutableListOf<Button>()
    private lateinit var error: TextView

    override fun onRetainNonConfigurationInstance(): Any = operation

    override fun onStart() {
        super.onStart()
        operation.observer = ::render
        render()
    }

    override fun onStop() {
        operation.observer = null
        super.onStop()
    }

    private fun render() {
        if (operation.status == Status.Applied) {
            setResult(RESULT_OK)
            finish()
            return
        }
        choices.forEach { it.isEnabled = operation.status != Status.Writing }
        error.visibility = if (operation.status == Status.Failed) View.VISIBLE else View.GONE
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        operation = lastNonConfigurationInstance as? ApplyOperation ?: ApplyOperation()
        onBackInvokedDispatcher.registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT) {
            if (operation.status != Status.Writing && operation.status != Status.Applied) finish()
        }
        fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()

        val scroll = ScrollView(this).apply {
            isFillViewport = true
            setBackgroundColor(Color.BLACK)
            setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.START or Gravity.CENTER_VERTICAL
        }
        error = TextView(this).apply {
            text = "Couldn’t apply wallpaper."
            setTextColor(Color.WHITE)
            setPaddingRelative(dp(24), dp(8), dp(24), dp(8))
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
            visibility = View.GONE
        }
        controls.addView(error)
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
            operation.start(applicationContext, flags)
        }
        addChoice("Lockscreen", R.drawable.ic_lockscreen) { applyWallpaper(WallpaperManager.FLAG_LOCK) }
        addChoice("Homescreen", R.drawable.ic_homescreen) { applyWallpaper(WallpaperManager.FLAG_SYSTEM) }
        addChoice("Both", R.drawable.ic_both) { applyWallpaper(WallpaperManager.FLAG_SYSTEM or WallpaperManager.FLAG_LOCK) }
        addChoice("Cancel", R.drawable.ic_cancel) { finish() }
        scroll.addView(controls)
        setContentView(scroll)
    }
}
