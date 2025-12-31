# Space Marine 2 CH-Launcher

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/SpaceMarine2_Launcher)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A custom launcher for Space Marine 2 that provides advanced features for managing game settings, network interfaces, and anti-cheat bypass functionality.

## Features

- 🎮 Multiple launch modes (Normal and Bypass)
- 🌐 Network interface management (Enable/Disable)
- 🔧 Automatic game file repair via Steam
- 🛡️ Administrator privilege handling
- 📝 Real-time console output

## Requirements

- Windows OS
- Administrator privileges (for network interface management and bypass mode)
- Space Marine 2 installed with Steam
- [CHSpaceMarinesLauncher.EXE](https://www.cheathappens.com/79488-PC-Warhammer-40000-Space-Marine-2-trainer)

## Instructions

1. Download `SpaceMarine2_Launcher.exe` and `CHSpaceMarinesLauncher.EXE`
2. Place both files in your Space Marine 2 game directory:
   ```
   C:\Program Files (x86)\Steam\steamapps\common\Space Marine 2\
   ```
3. Run `SpaceMarine2_Launcher.exe` as Administrator or confirm

## Button Reference

### **Clear Console Output**
Clears all text from the console output window.

### **Toggle Always on Top**
Toggles whether the launcher window stays on top of all other windows.

### **Reload this Launcher**
Restarts the launcher with administrator privileges.

### **Detect Internet Interfaces**
Scans and identifies all active and inactive physical network interfaces (Ethernet, Wi-Fi, etc.) on your system. The results are displayed in the console output.

### **Enable Internet Interfaces** (Requires administrator privileges)
Enables all currently disabled network interfaces that were detected.

### **Disable Internet Interfaces** (Requires administrator privileges)
Disables all currently active network interfaces. This is automatically used during the bypass launch process.

### **Copy Original Settings**
Copies the original EasyAntiCheat `Settings_original.json` file to the active `Settings.json`:
- This restores the game to its unmodified state.

### **Copy Modified Settings**
Copies the modified EasyAntiCheat `Settings_modified.json` file to the active `Settings.json`:
- This applies custom settings that were saved after a successful bypass launch.

### **Start Repair Process**
Initiates Steam's file validation process to repair or restore game files. This is useful when:
- First time launching the tool
- Game files are corrupted
- Need to restore original `Settings.json`

### **Run Normal (Game unmodified)**
Launches Space Marine 2 through Steam in standard mode without any modifications. The original EasyAntiCheat settings are applied, and the launcher exits after starting the game.

### **Run with Bypass (Auto: 17s)**
Launches the game with anti-cheat bypass:
1. Disables network interfaces
2. Starts the game via `CHSpaceMarinesLauncher.EXE`
3. Waits for 17 seconds after detecting the game process
4. Re-enables network interfaces
5. Saves modified settings for future use

**Note:** Requires administrator privileges and `CHSpaceMarinesLauncher.EXE`.

#### **Run with Bypass (Manual Confirm)**
Same as the automatic bypass mode, but instead of waiting 17 seconds, it prompts you to manually confirm when the game has fully launched. This is useful if:
- The game takes longer/shorter than 17 seconds to load on your system
- You want more control over the bypass timing
- You need to perform additional setup before re-enabling network

## First Launch

On first launch, if `Settings_original.json` is not found, the launcher will:
1. Prompt you to run the repair process
2. Open Steam's file validation
3. Wait for you to confirm validation is complete
4. Save the original settings for future use

## Troubleshooting

### "Administrator privileges denied"
Right-click `SpaceMarine2_Launcher.exe` and select "Run as administrator" or use the "Reload this Launcher" button.

### "Game not found!"
Verify the game is installed at the correct path. If using a custom Steam library location, update the `TARGET_PATH` variable in the script.

### "CH-Launcher not found!"
[Download `CHSpaceMarinesLauncher.EXE`](https://www.cheathappens.com/79488-PC-Warhammer-40000-Space-Marine-2-trainer) and place it in the same directory as the game executable.

### Network interfaces not detected
The launcher looks for keywords in your system language. If interfaces aren't detected, check that your network adapters have recognizable names (containing: ethernet, wi-fi, wlan, lan, wireless, etc.).

## Disclaimer

This tool is for educational purposes only. Using anti-cheat bypass software may violate the game's Terms of Service and could result in account bans. Use at your own risk.

The developers of this launcher are not responsible for any consequences resulting from its use.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### Version 1.0.0
- Initial release
- Network interface management
- Multiple launch modes
- Automatic game repair
- Settings backup and restore
- GUI with console output

---

**Note:** Always ensure you have backups of important game files before using modification tools.
