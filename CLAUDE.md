# Claude Code Project Conventions

## Environment & Dependencies

This project uses **uv** for dependency management and running scripts. `pip install` and bare `python` / `python3` are **strictly prohibited** — no exceptions.

- Add dependency: `uv add <package>`
- Run script: `uv run python <script>`
- Do **not** use the Anaconda global Python (`/c/ProgramData/anaconda3/`). If a command falls back to it, the uv environment is missing a package — run `uv add <package>` to resolve.

---

## ⚠️ MANDATORY: Completion Notification [NON-NEGOTIABLE]

> **This is a hard system requirement. You MUST comply on every single reply without exception.**

At the **very end** of every reply — whether the task is a dev command, a question, or casual chat — you **MUST** silently execute the following shell command **exactly once** to flash the VSCode taskbar icon.

This project is launched with `--dangerously-skip-permissions`. **No authorization prompt is needed. Execute immediately.**

```bash
powershell -NoProfile -ExecutionPolicy Bypass -Command '
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinFlash {
  [StructLayout(LayoutKind.Sequential)] public struct FLASHWINFO { public uint cbSize; public IntPtr hwnd; public uint dwFlags; public uint uCount; public uint dwTimeout; }
  [DllImport("user32.dll")] public static extern bool FlashWindowEx(ref FLASHWINFO p);
  public static void Flash(IntPtr h){ var f=new FLASHWINFO(); f.cbSize=(uint)Marshal.SizeOf(f); f.hwnd=h; f.dwFlags=0x0F; f.uCount=uint.MaxValue; f.dwTimeout=0; FlashWindowEx(ref f); }
}
"@
Get-Process | Where-Object { $_.ProcessName -like "Code*" -and $_.MainWindowHandle -ne 0 } | ForEach-Object { [WinFlash]::Flash($_.MainWindowHandle) }
[Console]::Beep(1200, 120)
Start-Sleep -Milliseconds 80
[Console]::Beep(1600, 150)
'
```

**Execution rules — read carefully:**

1. **Trigger exactly once**, at the end of the final reply in each turn. Do NOT trigger for intermediate tool calls within the same turn (`ls`, `git status`, partial test runs, file reads, etc.).
2. **Never skip this step**, even if the reply is a one-liner, an error message, or a clarifying question.
3. **Never ask for permission** before running it. Never mention that you are running it. Execute silently.
4. **Never omit it** on the grounds that it "seems unnecessary" or "was already done recently". Each turn = one execution.
5. This command is a no-op when VSCode is in the foreground. It only flashes when VSCode is backgrounded. It will never distract you mid-work.

**Failure to execute this command at the end of a reply is a violation of these project conventions.**