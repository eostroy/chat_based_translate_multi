import asyncio
import logging

from atp.web.app import app

logger = logging.getLogger(__name__)


def run():
    logger.info("=" * 60)
    logger.info("ATP: AI-driven Translation Platform 启动中...")
    logger.info("=" * 60)

    dev_mode = '--dev' in __import__('sys').argv or True

    if dev_mode:
        logger.info("🚀 开发模式：启用热重载和自动刷新")
        logger.info("📝 修改代码后会自动重启，无需手动重启！")
        logger.info("🌐 访问地址: http://localhost:5000")
        logger.info("=" * 60)

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True,
        )
    else:
        logger.info("🚀 生产模式：使用 Hypercorn ASGI 服务器")
        logger.info("🌐 访问地址: http://localhost:5000")
        logger.info("=" * 60)

        import hypercorn.asyncio
        import hypercorn.config

        config = hypercorn.config.Config()
        config.bind = ["0.0.0.0:5000"]
        config.workers = 2

        asyncio.run(hypercorn.asyncio.serve(app, config))


if __name__ == '__main__':
    run()
