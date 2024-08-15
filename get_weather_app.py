# -*- coding: utf-8 -*-
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
import matplotlib.pyplot as plt
import streamlit as st
import japanize_matplotlib
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import io


def get_weather(base_url, event_date):
    # 結果を格納するための空のDataFrameを作成
    result_df = pd.DataFrame()

    # 実績日を定義
    performance_date = datetime.strptime(event_date, '%Y-%m-%d')

    # 過去7日間の日付を計算
    dates = [performance_date - timedelta(days=i) for i in range(1, 8)]

    # 各日付に対して処理を実行
    for date in dates:
        first_url = f"{base_url}{date.strftime('%Y%m')}/{date.day}/"
        response = requests.get(first_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 次のページへのリンクを取得
        link_tag = soup.find('a', class_='link')
        if link_tag:
            next_url = urljoin(base_url, link_tag['href'])
            response = requests.get(next_url)
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            continue  # リンクがない場合、処理をスキップ

        # 指定された日付に一致するforecast-target-dateを探す
        forecasts = soup.find_all('div', class_='forecast card card-skin')
        for forecast in forecasts:
            forecast_date = forecast.find('div', class_='forecast-target-date')
            if forecast_date and forecast_date.text.strip() == performance_date.strftime('%m/%d'):
                # 天気予報と降水確率を取得
                weather_forecast = forecast.find('div', {'class': 'weather'}).text.strip()
                pop_num = forecast.find('div', {'class': 'pop-num'}).text.strip()
                pop_percent = forecast.find('div', {'class': 'pop-percent'}).text.strip()
                precipitation_probability = f"{pop_num}{pop_percent}"

                # 気温を取得
                highest_temperature = forecast.find('div', {'class': 'highest-temperature'}).text.strip()
                lowest_temperature = forecast.find('div', {'class': 'lowest-temperature'}).text.strip()

                # 結果をDataFrameに追加
                new_row = pd.DataFrame({
                    '実績日': [performance_date.date()],
                    '天気予報発表日': [date.date()],
                    '天気予報': [weather_forecast],
                    '降水確率': [precipitation_probability],
                    '最高気温': [highest_temperature],
                    '最低気温': [lowest_temperature]
                })
                result_df = pd.concat([result_df, new_row], ignore_index=True).sort_values(['実績日', '天気予報発表日'])

    return result_df


# 降水確率を処理する関数
def process_precipitation_probability(value):
    if '/' in value:
        numbers = list(map(int, value.replace('%', '').split('/')))
        return sum(numbers) / len(numbers)
    else:
        return int(value.replace('%', ''))


# グラフを描画する関数
def plot_temperature(df):
    df = df.copy()
    # '天気予報発表日'列をdatetime型に変換
    df['天気予報発表日'] = pd.to_datetime(df['天気予報発表日'])

    # '最高気温'と'最低気温'から '℃' を取り除き、数値に変換
    df['最高気温'] = df['最高気温'].str.replace('℃', '').astype(float)
    df['最低気温'] = df['最低気温'].str.replace('℃', '').astype(float)

    # '降水確率'を処理して数値に変換
    df['降水確率'] = df['降水確率'].apply(process_precipitation_probability)

    # プロットの作成
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 気温の線グラフ
    ax1.plot(df['天気予報発表日'], df['最高気温'], marker='o', label='最高気温')
    ax1.plot(df['天気予報発表日'], df['最低気温'], marker='o', label='最低気温')
    ax1.set_xlabel('天気予報発表日')
    ax1.set_ylabel('気温 (°C)')
    ax1.set_title('天気予報発表日ごとの最高気温,最低気温,降水確率,天気')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    # 降水確率の棒グラフ
    ax2 = ax1.twinx()
    ax2.bar(df['天気予報発表日'], df['降水確率'], color='blue', alpha=0.3, label='降水確率')
    ax2.set_ylim(0, 100)
    ax2.set_ylabel('降水確率 (%)')
    ax2.legend(loc='upper right')

    # 各天気に対応する画像を表示（グラフ枠外）
    for i, row in df.iterrows():
        if pd.notna(row['天気予報']):
            if '晴' in row['天気予報']:
                img = mpimg.imread('sunny_s_cloudy.png')
            elif '雨' in row['天気予報']:
                img = mpimg.imread('rainy_s_cloudy.png')
            elif '雪' in row['天気予報']:
                img = mpimg.imread('snowy.png')
            elif '曇' in row['天気予報']:
                img = mpimg.imread('cloudy.png')
            else:
                img = None

            if img is not None:
                imagebox = OffsetImage(img, zoom=0.8)
                # 降水確率0の少し上に画像を表示させるためにy座標を調整
                ab = AnnotationBbox(imagebox, (row['天気予報発表日'], 8), frameon=False)
                ax2.add_artist(ab)

    plt.tight_layout()
    return fig


# 気温のみを表示させる関数
def plot_temperature2(df):
    df = df.copy()
    # '天気予報発表日'列をdatetime型に変換
    df['天気予報発表日'] = pd.to_datetime(df['天気予報発表日'])

    # '最高気温'と'最低気温'から '℃' を取り除き、数値に変換
    df['最高気温'] = df['最高気温'].str.replace('℃', '').astype(float)
    df['最低気温'] = df['最低気温'].str.replace('℃', '').astype(float)

    # プロットの作成
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['天気予報発表日'], df['最高気温'], marker='o', label='最高気温')
    ax.plot(df['天気予報発表日'], df['最低気温'], marker='o', label='最低気温')

    # ラベルとタイトルの設定
    ax.set_xlabel('天気予報発表日')
    ax.set_ylabel('気温 (°C)')
    ax.set_title('天気予報発表日ごとの最高気温,最低気温')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # グラフの表示
    return fig


# 降水確率と天気を表示させる関数
def plot_temperature3(df):
    df = df.copy()
    # '天気予報発表日'列をdatetime型に変換
    df['天気予報発表日'] = pd.to_datetime(df['天気予報発表日'])

    # '最高気温'と'最低気温'から '℃' を取り除き、数値に変換
    df['最高気温'] = df['最高気温'].str.replace('℃', '').astype(float)
    df['最低気温'] = df['最低気温'].str.replace('℃', '').astype(float)

    # '降水確率'を処理して数値に変換
    df['降水確率'] = df['降水確率'].apply(process_precipitation_probability)

    # プロットの作成
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 降水確率の棒グラフ
    ax1.bar(df['天気予報発表日'], df['降水確率'], color='blue', alpha=0.3, label='降水確率')
    ax1.set_xlabel('天気予報発表日')
    ax1.set_ylim(0, 100)
    ax1.set_ylabel('降水確率 (%)')
    ax1.set_title('天気予報発表日ごとの降水確率と天気')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # 各天気に対応する画像を表示（グラフ枠外）
    for i, row in df.iterrows():
        if pd.notna(row['天気予報']):
            if '晴' in row['天気予報']:
                img = mpimg.imread('sunny_s_cloudy.png')
            elif '雨' in row['天気予報']:
                img = mpimg.imread('rainy_s_cloudy.png')
            elif '雪' in row['天気予報']:
                img = mpimg.imread('snowy.png')
            elif '曇' in row['天気予報']:
                img = mpimg.imread('cloudy.png')
            else:
                img = None

            if img is not None:
                imagebox = OffsetImage(img, zoom=0.8)
                # 降水確率0の少し上に画像を表示させるためにy座標を調整
                ab = AnnotationBbox(imagebox, (row['天気予報発表日'], 8), frameon=False)
                ax1.add_artist(ab)

    plt.tight_layout()
    return fig


# エリアと詳細エリアの辞書
area_display = {
    '北海道': {
        '稚内地方': '稚内地方気象台',
        '旭川地方': '旭川地方気象台',
        '網走地方': '網走地方気象台',
        '釧路地方': '釧路地方気象台',
        '室蘭地方': '室蘭地方気象台',
        '札幌管区': '札幌管区気象台',
        '函館地方': '函館地方気象台'
    },
    '東北': {
        '青森地方': '青森地方気象台',
        '盛岡地方': '盛岡地方気象台',
        '仙台管区': '仙台管区気象台',
        '秋田地方': '秋田地方気象台',
        '山形地方': '山形地方気象台',
        '福島地方': '福島地方気象台'
    },
    '関東甲信': {
        '水戸地方': '水戸地方気象台',
        '宇都宮地方': '宇都宮地方気象台',
        '前橋地方': '前橋地方気象台',
        '熊谷地方': '熊谷地方気象台',
        '銚子地方': '銚子地方気象台',
        '東京': '気象庁',
        '横浜地方': '横浜地方気象台',
        '甲府地方': '甲府地方気象台',
        '長野地方': '長野地方気象台'
    },
    '北陸': {
        '新潟地方': '新潟地方気象台',
        '富山地方': '富山地方気象台',
        '金沢地方': '金沢地方気象台',
        '福井地方': '福井地方気象台'
    },
    '東海': {
        '岐阜地方': '岐阜地方気象台',
        '静岡地方': '静岡地方気象台',
        '名古屋地方': '名古屋地方気象台',
        '津地方': '津地方気象台'
    },
    '近畿': {
        '彦根地方': '彦根地方気象台',
        '京都地方': '京都地方気象台',
        '大阪管区': '大阪管区気象台',
        '神戸地方': '神戸地方気象台',
        '奈良地方': '奈良地方気象台',
        '和歌山地方': '和歌山地方気象台'
    },
    '中国': {
        '鳥取地方': '鳥取地方気象台',
        '松江地方': '松江地方気象台',
        '岡山地方': '岡山地方気象台',
        '広島地方': '広島地方気象台',
        '下関地方': '下関地方気象台'
    },
    '四国': {
        '徳島地方': '徳島地方気象台',
        '高松地方': '高松地方気象台',
        '松山地方': '松山地方気象台',
        '高知地方': '高知地方気象台'
    },
    '九州': {
        '福岡管区': '福岡管区気象台',
        '佐賀地方': '佐賀地方気象台',
        '長崎地方': '長崎地方気象台',
        '熊本地方': '熊本地方気象台',
        '大分地方': '大分地方気象台',
        '宮崎地方': '宮崎地方気象台',
        '鹿児島地方': '鹿児島地方気象台'
    },
    '沖縄': {
        '沖縄': '沖縄気象台',
        '南大東島地方': '南大東島地方気象台',
        '宮古島地方': '宮古島地方気象台',
        '石垣島地方': '石垣島地方気象台'
    }
}

st.title('天気予報取得アプリ')

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
### このアプリについて

[テンマド](https://tenmado.app/weatherforecast/)から以下の情報を取得します:

- `実績日`: 天気予報の対象日
- `天気予報発表日`: 実績日の天気予報が発表された日
- `天気予報`: 予報された天気
- `降水確率`: 予報された降水確率
- `最高気温`: 予報された最高気温
- `最低気温`: 予報された最低気温
""")

また上記の情報をまとめたグラフを取得できます。

st.markdown("<hr>", unsafe_allow_html=True)

# エリア選択
selected_area = st.selectbox('エリアを選択してください', list(area_display.keys()))
# 詳細エリア選択
if selected_area:
    selected_place = st.selectbox('詳細エリアを選択してください', list(area_display[selected_area].keys()))
# 日付選択
event_date = st.date_input('日付を選択してください', datetime.today())

st.markdown("<hr>", unsafe_allow_html=True)

# セッションステートにデータを保持
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None

# セッションステートにデータを保持
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'place_list' not in st.session_state:
    st.session_state.place_list = None
if 'event_date_str' not in st.session_state:
    st.session_state.event_date_str = None

# 天気予報取得開始ボタンが押された場合
if st.button('天気予報取得開始'):
    if selected_place and event_date:
        with st.spinner('スクレイピング中'):
            st.session_state.event_date_str = event_date.strftime('%Y-%m-%d')
            base_url = 'https://tenmado.app/weatherforecast/'
            
            # 選択された場所をアンダースコアで連結した文字列に変換
            st.session_state.place_list = selected_place
            
            # 天気予報データの取得とセッションステートへの保存
            st.session_state.weather_data = get_weather(
                f"{base_url}{area_display[selected_area][selected_place]}/", st.session_state.event_date_str
            )
            
            # データフレームが空かどうかをチェック
            if st.session_state.weather_data.empty:
                st.error('該当するデータが見つかりませんでした')
            else:
                st.write('天気予報取得完了')

st.markdown("<hr>", unsafe_allow_html=True)

# データがセッションステートに保存されている場合は表示
if st.session_state.weather_data is not None and not st.session_state.weather_data.empty:
    df = st.session_state.weather_data
    st.dataframe(df)

    # CSVのダウンロードボタン
    csv = df.to_csv(index=False, encoding='shift_jis', errors='ignore')
    st.download_button(
        label='天候情報をCSVとしてダウンロード',
        data=csv,
        file_name=f'weather_{st.session_state.place_list}_{event_date.strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    try:
        # fig1のプロットとダウンロードボタン
        fig1 = plot_temperature(df)
        st.pyplot(fig1)
        
        # Figureをバッファに保存
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format="png")
        buf1.seek(0)
        
        st.download_button(
            label="気温+降水確率plotをダウンロード",
            data=buf1,
            file_name=f'overall_{st.session_state.place_list}_{event_date.strftime("%Y%m%d")}.png',
            mime='image/png'
        )
        buf1.close()
    except KeyError:
        st.error('該当するデータが見つかりませんでした')

    st.markdown("<hr>", unsafe_allow_html=True)

    try:
        # fig2のプロットとダウンロードボタン
        fig2 = plot_temperature2(df)
        st.pyplot(fig2)

        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png")
        buf2.seek(0)

        st.download_button(
            label="気温plotをダウンロード",
            data=buf2,
            file_name=f'temperature_{st.session_state.place_list}_{event_date.strftime("%Y%m%d")}.png',
            mime='image/png'
        )
        buf2.close()
    except KeyError:
        st.error('該当するデータが見つかりませんでした')

    st.markdown("<hr>", unsafe_allow_html=True)

    try:
        # fig3のプロットとダウンロードボタン
        fig3 = plot_temperature3(df)
        st.pyplot(fig3)

        buf3 = io.BytesIO()
        fig3.savefig(buf3, format="png")
        buf3.seek(0)
        
        st.download_button(
            label="降水確率plotをダウンロード",
            data=buf3,
            file_name=f'chanceofrain_{st.session_state.place_list}_{event_date.strftime("%Y%m%d")}.png',
            mime='image/png'
        )
        buf3.close()
    except KeyError:
        st.error('該当するデータが見つかりませんでした')
