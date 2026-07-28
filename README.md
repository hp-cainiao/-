# CobaltStarPet / 钴星

这是 Codex 宠物的钴星展示仓库。根目录展示各状态 GIF，`hatch-cobalt-star/final/` 提供可安装宠物包，`hatch-cobalt-star/qa/` 提供 QA 总览和方向检查图。

## 效果展示

| 状态          | 预览                                |
| ------------- | ----------------------------------- |
| Idle          | ![idle](idle.gif)                   |
| Running       | ![running](running.gif)             |
| Running Left  | ![running-left](running-left.gif)   |
| Running Right | ![running-right](running-right.gif) |
| Waving        | ![waving](waving.gif)               |
| Jumping       | ![jumping](jumping.gif)             |
| Waiting       | ![waiting](waiting.gif)             |
| Failed        | ![failed](failed.gif)               |
| Review        | ![review](review.gif)               |

## 仓库内容

```text
.
├── idle.gif / running.gif / ...       # 钴星 spritesheet 提取的状态 GIF
├── build_from_local_cobalt_star.py    # 本仓库素材
├── hatch-cobalt-star/
│   ├── pet_request.json               # 宠物元信息和来源记录
│   ├── final/
│   │   ├── spritesheet.webp           # 可安装到 Codex 的 v2 spritesheet
│   │   ├── pet.json                   # Codex 宠物配置
│   │   └── validation.json            # 本仓库生成的校验结果
│   └── qa/
│       ├── contact-sheet.png          # 9 个标准状态展示
│       ├── contact-sheet-extended.png # 11 行 v2 完整展示
│       ├── look-directions.png        # 16 个看向方向展示
│       ├── previews/*.gif             # 带棋盘背景的状态预览
│       └── run-summary.json
└── README.md
```

## 安装到 Codex

Codex 默认使用 `~/.codex` 作为用户数据目录；如果你设置了 `CODEX_HOME`，请把下面命令里的 `~/.codex` 替换成你的 `CODEX_HOME` 路径。

```bash
mkdir -p ~/.codex/pets/cobalt-star
cp hatch-cobalt-star/final/spritesheet.webp ~/.codex/pets/cobalt-star/spritesheet.webp
cp hatch-cobalt-star/final/pet.json ~/.codex/pets/cobalt-star/pet.json
```

Windows 示例目录：

```text
C:\Users\<你的用户名>\.codex\pets\cobalt-star
```

目录内需要同时包含：

```text
spritesheet.webp
pet.json
```

## 校验信息

最终 v2 宠物素材位于：

```text
hatch-cobalt-star/final/spritesheet.webp
hatch-cobalt-star/final/pet.json
```

本仓库校验结果：

```text
hatch-cobalt-star/final/validation.json
```
