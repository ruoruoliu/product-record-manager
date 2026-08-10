# 产品记录管理系统 (Product Record Manager)

这是一个用于管理工厂生产记录的在线 Web 应用程序。

## 本地开发

```bash
FLASK_DEBUG=1 python app.py
```
默认访问地址：http://127.0.0.1:5792

## 生产部署

服务通过 systemd + waitress 运行在 VPS 上，监听 5792 端口。

## 文件结构说明
- `app.py`: 核心应用程序代码。
- `templates/`: 网页 HTML 模板。
- `pyproject.toml`: 项目依赖配置。
