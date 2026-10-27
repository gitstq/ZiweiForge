# ZiweiForge —— 常用开发任务
# 全部目标仅依赖 Python 标准库，无需安装任何第三方包。

PY      ?= python3
PKG     := ziweiforge

.PHONY: help install test lint build sdist wheel clean demo

help:                      ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n",$$1,$$2}'

install:                   ## 以可编辑模式安装到当前环境
	$(PY) -m pip install -e .

test:                      ## 运行全量自测（标准库 unittest）
	$(PY) -m unittest discover -s tests -v

lint:                      ## 语法与导入检查（不引入 flake8 等外部工具）
	$(PY) -m compileall -q $(PKG) tests examples
	$(PY) -c "import $(PKG); print('import ok:', $(PKG).__version__)"

demo:                      ## 运行内置示例
	$(PY) examples/basic.py

build: sdist wheel         ## 构建源码包与 wheel

sdist:                     ## 构建源码分发包
	$(PY) -m build --sdist .

wheel:                     ## 构建 wheel
	$(PY) -m build --wheel .

clean:                     ## 清理构建产物与缓存
	rm -rf build dist *.egg-info .pytest_cache examples/out
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
