# NitroCore - Windows System Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**NitroCore** is a professional Windows system optimization utility that helps boost gaming and application performance by cleaning temporary files, optimizing registry settings, managing services, and tuning system performance.

## 🚀 Features

- **Registry Optimization**: Safely optimize Windows registry for better performance
- **Temporary File Cleanup**: Remove temporary files and browser cache
- **Disk Cleanup**: Free up disk space by cleaning system files
- **Service Management**: Disable unnecessary services to improve performance
- **Performance Tuning**: Apply Windows performance tweaks
- **User-Friendly GUI**: Clean, intuitive tabbed interface
- **Logging System**: Comprehensive logging for troubleshooting
- **Error Handling**: Robust error handling with detailed feedback
- **Progress Tracking**: Real-time progress updates during operations

## 📋 Requirements

- Python 3.8 or higher
- Windows 7, 8, 10, or 11
- Administrator privileges
- PyYAML >= 6.0.0
- psutil >= 5.8.0
- pywin32 >= 300 (for Windows service management)

## 🔧 Installation

### From Source

```bash
git clone https://github.com/thedarkonejesus/Nitrocore.git
cd NitroCore
pip install -r requirements.txt
python -m NitroCore.source.main
```

## 🎯 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thedarkonejesus/Nitrocore.git
   cd NitroCore
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run as Administrator**:
   ```bash
   python -m NitroCore.source.main
   ```

## 📖 Usage

### GUI Application

Launch the application with:
```bash
python -m NitroCore.source.main
```

The application features several tabs:

- **Registry**: Optimize Windows registry settings
- **Temporary Files**: Clean temporary files and browser cache
- **Disk Cleanup**: Remove system temporary files
- **Services**: Manage background services
- **Performance**: Apply system performance tweaks
- **Status**: View detailed status and logs

## 🔒 Security Considerations

- **Administrator Privileges**: The application requires admin rights to modify system settings
- **Backup**: Always create a system restore point before running optimizations
- **Testing**: Test on a non-critical system first
- **Logging**: All operations are logged for audit trail

## ⚠️ Warnings

- **System Modifications**: This tool modifies Windows registry and system files
- **Data Loss Risk**: Be cautious with aggressive cleanup options
- **Service Disruption**: Disabling certain services may affect system functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

This tool is provided as-is without warranty. Use at your own risk and always maintain backups.

---

**Made with ❤️ for Windows users**
