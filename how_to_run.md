使用方法：
- Windows 用户：运行 .\setup.bat
- Linux/Mac 用户：运行 chmod +x setup.sh && ./setup.sh

按照提示激活环境：
- Windows的PowerShell:  .\.venv\Scripts\Activate.ps1
- Windows的cmd:         .venv\Scripts\activate.bat
- Linux/Mac:            source venv/bin/activate

用户运行测试：
# Windows
python -m surface_code_study.tests.test_sanity

# Linux/Mac
python -m surface_code_study.tests.test_sanity

实验结果展示：在results文件夹中