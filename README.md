# 产品记录管理系统 (Product Record Manager)

这是一个用于管理工厂生产记录的本地 Web 应用程序。

本项目已配置特定的打包脚本，允许您**在 macOS 上直接生成**一个可以在**离线 Windows 电脑**上直接运行的免安装包。

## 如何制作 Windows 免安装包

您不需要 Windows 电脑，也不需要手动下载 Python，只需在您的 Mac 上执行以下步骤：

1.  **运行打包脚本**：
    打开终端，运行：
    ```bash
    ./build_portable_mac.sh
    ```
    *该脚本会自动下载 Windows 版的 Python 核心和所有依赖库，并将其组装在一起。*

2.  **获取结果**：
    脚本运行完成后，会在项目根目录下生成一个 `dist_portable` 文件夹，里面有一个 `ProductManager` 文件夹。

3.  **发送给用户**：
    *   将 `dist_portable/ProductManager` 文件夹压缩成 Zip 包。
    *   通过 U 盘或其他方式发送给用户。

## 用户如何使用（Windows 端）

用户收到文件后，操作非常简单（傻瓜式）：

1.  **解压**您发送的压缩包。
2.  进入文件夹，双击 **`管理系统.bat`**。
3.  系统会自动启动，并自动打开浏览器显示管理界面。

> **注意**：用户电脑**不需要**联网，也**不需要**安装 Python，直接双击即可运行。

## 开发与运行（Mac 本地）

如果您想在自己的 Mac 上开发或运行：

```bash
python app.py
```
默认访问地址：http://127.0.0.1:5792

## 文件结构说明
- `app.py`: 核心应用程序代码。
- `build_portable_mac.sh`: **核心脚本**，用于一键制作 Windows 免安装包。
- `templates/`: 网页 HTML 模板。
- `static/`: 静态资源文件（CSS/JS）。
- `dist_portable/`: 打包生成的输出目录（平时可忽略）。
