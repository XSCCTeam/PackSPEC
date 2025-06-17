#!/bin/bash

set -e

# 定义提示等级label
# 修改颜色定义部分，使用更兼容的tput命令
INFO_LABEL="$(tput setaf 4)[INFO]$(tput sgr0)"
ATTENTION_LABEL="$(tput setaf 1)[ATTENTION]$(tput sgr0)"
DEBUG_LABEL="$(tput setaf 3)[DEBUG]$(tput sgr0)"
SUCCESS_LABEL="$(tput setaf 2)[SUCCESS]$(tput sgr0)"

SPEC06_REPO_URL="git@172.38.10.144:linwang/spec2006-tar.git"
SPEC17_REPO_URL="git@172.38.10.144:linwang/spec2017-iso.git"

# 定义LLVM安装路径
LLVM_INSTALL_PATH=/home/wll/BOSC/XSCC-x86-bin

# 定义项目路径
PROJECT_DIR="$(cd "$(dirname "$0")/../" && pwd)"
# 定义测试路径
TEST_DIR="$PROJECT_DIR/tests"
# 定义测试空间路径
TEST_SPACE_DIR="$TEST_DIR/test_space"
# 定义测试检查脚本路径
CHECK_TEST=$TEST_DIR/check_tests.py
# 定义测试log路径
TEST_LOG_DIR="$TEST_SPACE_DIR/logs"
mkdir -p $TEST_LOG_DIR
TODAY=$(date +%y%m%d-%H%M%S)
LOG_FILE=$TEST_LOG_DIR/install-$TODAY.log
# 定义PackSPEC路径
PACK_SPEC_DIR=$TEST_SPACE_DIR/pack_spec
###############################################
#  SPEC cpu 2006
###############################################
# 定义SPEC06路径
SPEC06_DIR="$TEST_SPACE_DIR/SPEC06"
# 定义SPEC06安装路径
SPEC06_INSTALL_DIR=$SPEC06_DIR/speccpu2006-v1.0.1
# 定义SPEC06 cfg路径
SPEC06_CFGS=$TEST_DIR/spec06_cfgs
# 定义SPEC06 cfg
SPEC06_CONFIG=x86_llvm19_novec.cfg
# 定义SPEC06 setup脚本
SPEC06_SETUP=setup_spec06.py
# 定义SPEC06 tests
SPEC06_TESTS=$TEST_DIR/spec06_tests
# 定义SPEC06 tests out
SPEC06_TESTS_OUT=$TEST_SPACE_DIR/spec06_tests_out

###############################################
#  SPEC cpu 2017
###############################################
# 定义SPEC17路径
SPEC17_DIR="$TEST_SPACE_DIR/SPEC17"
# 定义SPEC17安装路径
SPEC17_INSTALL_DIR=$SPEC17_DIR/speccpu2017-v1.0.2
# 定义SPEC17 cfg路径
SPEC17_CFGS=$TEST_DIR/spec17_cfgs
# 定义SPEC17 cfg
SPEC17_CONFIG=x86_llvm19_novec.cfg
# 定义SPEC17 setup脚本
SPEC17_SETUP=setup_spec17.py
# 定义SPEC17 tests
SPEC17_TESTS=$TEST_DIR/spec17_tests
# 定义SPEC17 tests out
SPEC17_TESTS_OUT=$TEST_SPACE_DIR/spec17_tests_out

function clean(){
    echo -e "$INFO_LABEL Cleaning PackSPEC test space..."
    if [ -d "$SPEC06_DIR" ]; then
        echo -e "$INFO_LABEL Remove spec06_dir on $SPEC06_DIR"
        rm -rf $SPEC06_DIR
    else
        echo -e "$INFO_LABEL spec06_dir not found on $SPEC06_DIR"
    fi

    if [ -d "$SPEC17_DIR" ]; then
        echo -e "$INFO_LABEL Remove SPEC17_DIR on $SPEC17_DIR"
        sudo rm -rf $SPEC17_DIR
    else
        echo -e "$INFO_LABEL SPEC17_DIR not found on $SPEC17_DIR"
    fi
}

function update_pack_spec(){
    if [ -d "$PACK_SPEC_DIR" ]; then
        echo -e "$INFO_LABEL Updating PackSPEC..."
        rm -rf $PACK_SPEC_DIR
        cd $PROJECT_DIR
        rsync -a --exclude-from=.gitignore $PROJECT_DIR/ $PACK_SPEC_DIR/
        cd $PACK_SPEC_DIR
        cp $PACK_SPEC_DIR/config.py.example $PACK_SPEC_DIR/config.py
    fi
}

function init(){
    echo -e "$INFO_LABEL Initializing PackSPEC test space..."
    if ! command -v git-lfs &> /dev/null; then
        echo -e "$INFO_LABEL Install git-lfs locally..."
        # 创建本地安装目录
        LOCAL_BIN="$HOME/.local/bin"
        mkdir -p "$LOCAL_BIN"
        # 下载最新版本的git-lfs
        GIT_LFS_VERSION=$(curl -s https://api.github.com/repos/git-lfs/git-lfs/releases/latest | grep "tag_name" | cut -d '"' -f 4)
        wget -q https://ghfast.top/https://github.com/git-lfs/git-lfs/releases/download/$GIT_LFS_VERSION/git-lfs-linux-amd64-$GIT_LFS_VERSION.tar.gz
        mkdir git-lfs-$GIT_LFS_VERSION
        tar -xzf git-lfs-linux-amd64-$GIT_LFS_VERSION.tar.gz -C git-lfs-$GIT_LFS_VERSION --strip-components=1
        # 安装到本地目录
        mv git-lfs-$GIT_LFS_VERSION/git-lfs "$LOCAL_BIN"
        # 清理下载文件
        rm -rf git-lfs-$GIT_LFS_VERSION git-lfs-linux-amd64-$GIT_LFS_VERSION.tar.gz
        # 添加本地bin目录到PATH
        export PATH="$LOCAL_BIN:$PATH"
        git lfs install
    fi

    if [ ! -d "$PACK_SPEC_DIR" ]; then
        echo -e "$INFO_LABEL Initializing PackSPEC..."
        cd $PROJECT_DIR
        rsync -a --exclude-from=.gitignore $PROJECT_DIR/ $PACK_SPEC_DIR/
        cd $PACK_SPEC_DIR
        cp $PACK_SPEC_DIR/config.py.example $PACK_SPEC_DIR/config.py
    else
        if [ -n "$(ls -A $PACK_SPEC_DIR/packed_files 2>/dev/null)" ]; then
            echo -e "$INFO_LABEL Cleaning $PACK_SPEC_DIR/packed_files..."
            rm -rf $PACK_SPEC_DIR/packed_files
        fi
        echo -e "$INFO_LABEL PackSPEC already initialized."
    fi

    if [ ! -d "$SPEC06_DIR" ]; then
        echo -e "$INFO_LABEL Initializing repository..."
        cd $TEST_SPACE_DIR
        git clone $SPEC06_REPO_URL SPEC06
        echo -e "$INFO_LABEL Repository initialized."
    else
        echo -e "$INFO_LABEL Repository already initialized."
    fi

    if [ ! -d "$SPEC06_INSTALL_DIR" ]; then
        echo -e "$INFO_LABEL Unpacking spec06..."
        cd $SPEC06_DIR
        tar -zxvf speccpu2006-v1.0.1.tar.gz
        cd $SPEC06_INSTALL_DIR
        echo -e "$INFO_LABEL remove config/*.cfg."
        rm config/*.cfg
        echo -e "$INFO_LABEL spec06 unpacked."
        echo -e "$ATTENTION_LABEL Installing spec06..."
        cd $SPEC06_INSTALL_DIR
        echo -e "$INFO_LABEL Select 'linux-suse101-AMD64' ..."
        ./install.sh <<< "linux-suse101-AMD64"
    else
        echo -e "$INFO_LABEL spec06 already Installed."
        echo -e "$INFO_LABEL Initializing spec06..."
        cd $SPEC06_INSTALL_DIR
        cp $SPEC06_CFGS/$SPEC06_CONFIG $SPEC06_INSTALL_DIR/config/
        source shrc
        runspec -c $SPEC06_CONFIG -a scrub all
        echo -e "$INFO_LABEL remove result/*."
        if [ -n "$(ls -A result/ 2>/dev/null)" ]; then
            echo -e "$INFO_LABEL remove result/*."
            rm -rf result/*
        fi
        if [ -n "$(ls -A config/*.cfg 2>/dev/null)" ]; then
            echo -e "$INFO_LABEL remove config/*.cfg."
            rm config/*.cfg
        fi
        echo -e "$INFO_LABEL Initial spec06 done."
    fi

    if [ ! -d "$SPEC17_DIR" ]; then
        echo -e "$INFO_LABEL Initializing repository..."
        cd $TEST_SPACE_DIR
        git clone $SPEC17_REPO_URL SPEC17
        echo -e "$INFO_LABEL Repository initialized."
    else
        echo -e "$INFO_LABEL Repository already initialized."
    fi

    if [ ! -d "$SPEC17_INSTALL_DIR" ]; then
        echo -e "$INFO_LABEL Unpacking spec17..."
        cd $SPEC17_DIR
        echo -e "$INFO_LABEL Unpack spec17 to speccpu2017-v1.0.2 ..."
        mkdir -p speccpu2017-v1.0.2
        bsdtar -xf cpu2017-1_0_2.iso -C speccpu2017-v1.0.2
        cd $SPEC17_INSTALL_DIR
        echo -e "$INFO_LABEL Spec17 unpacked."
        echo -e "$ATTENTION_LABEL Installing spec17..."
        cd $SPEC17_INSTALL_DIR
        ./install.sh <<< "yes"
    else
        echo -e "$INFO_LABEL spec17 already Installed."
        echo -e "$INFO_LABEL Initializing spec17..."
        cd $SPEC17_INSTALL_DIR
        cp $SPEC17_CFGS/$SPEC17_CONFIG $SPEC17_INSTALL_DIR/config/
        source shrc
        runcpu -c $SPEC17_CONFIG -a scrub all
        echo -e "$INFO_LABEL remove result/*."
        if [ -n "$(ls -A result/ 2>/dev/null)" ]; then
            echo -e "$INFO_LABEL remove result/*."
            rm -rf result/*
        fi
        if [ -n "$(ls -A config/Example-*.cfg 2>/dev/null)" ]; then
            echo -e "$INFO_LABEL Remove config/*.cfg."
            # 删除config目录下所有不以Example-开头的.cfg文件
            find config -name "*.cfg" ! -name "Example-*.cfg" -type f -delete
        fi
        echo -e "$INFO_LABEL Initial spec17 done."
    fi
}

function setup_spec06(){
    echo -e "$INFO_LABEL Setting up spec06..."
    echo -e "$INFO_LABEL Copying $SPEC06_CONFIG to $SPEC06_CONFIG_DIR"
    cp $SPEC06_CFGS/$SPEC06_CONFIG $SPEC06_INSTALL_DIR/config/
    echo -e "$INFO_LABEL Copying $SPEC06_SETUP to $PACK_SPEC_DIR"
    cp $TEST_DIR/$SPEC06_SETUP $PACK_SPEC_DIR

    cd $PACK_SPEC_DIR
    export LLVM_INSTALL_PATH=$LLVM_INSTALL_PATH
    export SPEC2006_DIR=$SPEC06_INSTALL_DIR
    python $SPEC06_SETUP
}


function setup_spec17(){
    echo -e "$INFO_LABEL Setting up spec17..."
    echo -e "$INFO_LABEL Copying $SPEC17_CONFIG to $SPEC17_CONFIG_DIR"
    cp $SPEC17_CFGS/$SPEC17_CONFIG $SPEC17_INSTALL_DIR/config/
    echo -e "$INFO_LABEL Copying $SPEC17_SETUP to $PACK_SPEC_DIR"
    cp $TEST_DIR/$SPEC17_SETUP $PACK_SPEC_DIR

    cd $PACK_SPEC_DIR
    export LLVM_INSTALL_PATH=$LLVM_INSTALL_PATH
    export SPEC2017_DIR=$SPEC17_INSTALL_DIR
    python $SPEC17_SETUP
}

function test_spec06(){
    echo -e "$INFO_LABEL Testing spec06..."
    cd $PACK_SPEC_DIR
    cp $SPEC06_TESTS/* $PACK_SPEC_DIR
    mkdir -p $SPEC06_TESTS_OUT
    export SPEC2006_DIR=$SPEC06_INSTALL_DIR
    for script in $PACK_SPEC_DIR/test06*.py; do
        if [ -f "$script" ]; then
            script_name=$(basename "$script" .py)
            echo -e "$INFO_LABEL Running $script_name.py ..."
            python "$script" > "$SPEC06_TESTS_OUT/${script_name}.log" 2>&1
            python $CHECK_TEST --test_path $script --test_out_path $SPEC06_TESTS_OUT/${script_name}.log
        fi
    done
}

case "$1" in
    --init)
        init 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Init done." | tee -a $LOG_FILE
        exit 0
        ;;
    --update)
        update_pack_spec 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Update PackSPEC done." | tee -a $LOG_FILE
        exit 0
        ;;
    --setup06)
        setup_spec06 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Setup spec2006 done." | tee -a $LOG_FILE
        exit 0
        ;;
    --setup17)
        setup_spec17 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Setup spec2017 done." | tee -a $LOG_FILE
        exit 0
        ;;
    --test06)
        test_spec06 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Test spec2006 done." | tee -a $LOG_FILE
        exit 0
        ;;
    --clean)
        clean 2>&1 | tee -a $LOG_FILE
        echo -e "$SUCCESS_LABEL Clean done." | tee -a $LOG_FILE
        exit 0
        ;;
    *)
        echo -e "$ATTENTION_LABEL Usage: $1 --init | --update | --setup06 | --setup17 | --test06 | --clean"
        echo -e "$ATTENTION_LABEL 请使用--init初始化测试环境 | --update 更新PackSPEC | --setup06 编译spec2006 | --setup17 编译spec2017 | --test06 测试spec2006 | --clean 清理测试环境"
        exit 0
        ;;
esac
