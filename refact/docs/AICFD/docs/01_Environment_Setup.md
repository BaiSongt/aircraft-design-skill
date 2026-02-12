# 详细环境安装与验证指南

## 1. 操作系统

*   **推荐**: **Ubuntu 20.04/22.04 LTS**。这是OpenFOAM和许多科学计算库的官方支持和最佳运行平台。
*   **Windows用户**: 安装 **WSL 2 (Windows Subsystem for Linux)** 并从Microsoft Store安装Ubuntu 22.04。后续所有操作都在WSL 2的Ubuntu环境中进行。

## 2. OpenFOAM 安装

我们将安装 OpenFOAM.org 发布的版本。

```bash
# 更新包列表
sudo apt-get update

# 安装依赖
sudo apt-get install -y build-essential flex bison cmake zlib1g-dev libboost-system-dev libboost-thread-dev libopenmpi-dev openmpi-bin gnuplot

# 从官方源安装OpenFOAM (以v11为例)
# 添加OpenFOAM的仓库
curl -s https://dl.openfoam.org/pubkey.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/openfoam.gpg
sudo add-apt-repository "deb https://dl.openfoam.org/ubuntu focal main"
sudo apt-get update

# 安装OpenFOAM-v11
sudo apt-get install -y openfoam11
```

*   **配置环境**: 将以下行添加到你的 `~/.bashrc` 文件中。

```bash
echo "source /usr/lib/openfoam/openfoam11/etc/bashrc" >> ~/.bashrc
source ~/.bashrc
```

*   **验证安装**: 在终端输入 `simpleFoam -help`，如果看到帮助信息，则表示安装成功。

## 3. Gmsh 安装 (用于网格生成)

```bash
# 使用apt安装
sudo apt-get install -y gmsh

# 验证安装
gmsh --version
```

## 4. Python 环境 (使用Miniconda)

使用Conda可以创建独立的Python环境，避免包依赖冲突。

```bash
# 下载并安装Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# 按照提示完成安装，并重启终端

# 创建一个新的conda环境
conda create --name aicfd python=3.9 -y

# 激活环境
conda activate aicfd
```

*   **安装核心Python库**: 创建一个名为 `requirements.txt` 的文件，内容如下：

```text
numpy
pandas
matplotlib
scipy
scikit-learn
pyfoam
gmsh
torch
jupyterlab
fastapi
uvicorn
python-multipart
```

*   **执行安装**:

```bash
pip install -r requirements.txt
```

## 5. 环境综合验证

这一步至关重要，确保所有工具都能协同工作。

1.  **准备一个模板案例**: 从OpenFOAM的教程中复制一个简单案例，如 `incompressible/simpleFoam/pitzDaily`。
    ```bash
    # 创建工作目录
    mkdir -p ~/aicfd_workspace/cases
    cd ~/aicfd_workspace/cases

    # 复制教程案例
    cp -r $FOAM_TUTORIALS/incompressible/simpleFoam/pitzDaily .
    cd pitzDaily
    ```
2.  **手动运行案例**:
    ```bash
    # 生成网格
    blockMesh

    # 运行求解器
    simpleFoam

    # 检查结果
    ls -l postProcessing/
    ```
    如果 `postProcessing` 文件夹内有结果，说明OpenFOAM工作正常。

3.  **Python脚本验证**:
    *   **Gmsh API**: 运行Python，输入 `import gmsh; gmsh.initialize(); gmsh.finalize()`，如果不报错，说明API可用。
    *   **PyFoam**: 在终端运行 `pyFoamClearCase.py --help`，如果显示帮助信息，说明PyFoam安装成功。

完成以上所有步骤后，你的开发环境就准备就绪了。所有组件都已安装并验证可以独立工作，为后续的自动化集成打下了坚实的基础。
