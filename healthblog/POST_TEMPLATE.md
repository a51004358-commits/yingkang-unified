# 健康庫文章模板（未來每日帖）

靜態 HTML：複製最近一篇 `posts/YYYY-MM-DD-*.html`，改標題／正文／圖，再插入「推薦產品」。

## 必做：推薦產品區塊

每篇可推薦 **1–2 個**相關產品（browse-first，無購買按鈕、無價格）。

放在返回健康庫／WhatsApp CTA **之前**（文章正文之後）。

```bash
# 依標題關鍵字建議產品，並印出 HTML
python3 scripts/healthblog_rec_product.py --pick "秋涼換季鼻部不適"

# 或指定產品 slug 印出區塊
python3 scripts/healthblog_rec_product.py --print biyan-60caps-mk368
```

把輸出的 `<!-- hb-rec:start -->…<!-- hb-rec:end -->` 貼進文章。

主題對照（browse-first，無購買按鈕、無價格；功效與搜尋關鍵字可自由書寫）：

| 主題關鍵字 | 建議產品 |
|---|---|
| 鼻／換季／噴霧 | 鼻炎素 `biyan-60caps-mk368` |
| 膏布／貼敷 | 金門一條根膏布 `jinmen-yitiaogen-zuogu-gaobu-10pcs-yk401` |
| 口服／養生 | 強力炎必清 `yanbiqing-60caps-y5` |
| 睡眠 | 想睡就睡 `xiangshui-50caps-k0035` |
| 消化／開胃 | 花塔糖 `huatatang-50caps-x4-yk470` |
| 肩頸 | 八岐蛇肩頸油 `baqi-she-jianjing-cigu-oil-50ml-mk383` |
| 腰背／久坐 | 坐骨神經膏布 `zuogu-gaobu-10pcs-x11-yk400` |
| 關節／轉涼 | 風澀骨剌丹 `fengse-gucidan-60caps-k0002` |
| 皮膚／保濕 | 滴膚堅 `difugen-15ml-yk395` |
| 疲勞／午後 | 蕥歡仙 `yahuanxian-60caps-k0038` |
| 眼睛／螢幕 | 膚特靈噴霧 `futeiling-120ml-yk404` |

新增對照時：編輯 `scripts/healthblog_rec_product.py` 的 `PRODUCTS`、`POST_PRODUCT`、`THEME_KEYWORDS`，再跑一次腳本。

CSS：`assets/site.css` 的 `.hb-rec*`；文章內 `site.css?v=` 請與腳本 `CSS_VER` 一致。

| 腿／通勤緩衝 | 健步虎潛丸 `jianbu-huqian-320caps-mk370` |
| 台灣一條根大片 | 台灣一條根膏布 20片 `taiwan-yitiaogen-zuogu-gaobu-20pcs-k0025` |

跑全量注入（含雙推薦）：

```bash
python3 scripts/healthblog_rec_product.py
python3 scripts/healthblog_rec_product.py --list
```

