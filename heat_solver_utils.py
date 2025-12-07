"""
Heat Flow Solver - Python Utility Functions
Sui言語からFFIで呼び出されるユーティリティ関数群
"""

import json
import csv
from typing import Tuple, Dict, Any


def get_equipment_count(config_file: str = "equipment_config.json") -> int:
    """
    ①機器構成データ読み取り：ヒートポンプの台数を返す
    
    Args:
        config_file: 機器構成JSONファイルのパス
    
    Returns:
        int: ヒートポンプの台数（＝冷水ポンプの台数）
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['heat_pumps']['count']


def read_timeseries_t2(csv_file: str = "timeseries.csv", timestamp: str = "") -> float:
    """温度(t2)のみを返す"""
    t2, _ = read_timeseries(csv_file, timestamp)
    return t2


def read_timeseries_f2(csv_file: str = "timeseries.csv", timestamp: str = "") -> float:
    """流量(F2)のみを返す"""
    _, f2 = read_timeseries(csv_file, timestamp)
    return f2


def read_timeseries(csv_file: str = "timeseries.csv", timestamp: str = "") -> Tuple[float, float]:
    """
    ②時系列データ読み取り：指定時刻の温度と流量を返す
    
    Args:
        csv_file: 時系列データCSVファイルのパス
        timestamp: タイムスタンプ文字列（例: "202512071900"）
    
    Returns:
        tuple: (温度, 流量) = (t2, F2)
    
    Raises:
        ValueError: 指定されたタイムスタンプが見つからない場合
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['time'] == timestamp:
                return float(row['t2']), float(row['F2'])
    
    raise ValueError(f"Timestamp {timestamp} not found in {csv_file}")


def get_hp_characteristics(config_file: str = "equipment_config.json") -> Tuple[float, ...]:
    """
    ③ヒートポンプ特性データ読み取り
    
    Args:
        config_file: 機器構成JSONファイルのパス
    
    Returns:
        tuple: (p0, p20, p40, p60, p80, p100, t_supply, load_min, load_max)
               負荷率0-100%の消費電力6点 + 出口温度 + 負荷上下限
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    hp = config['heat_pumps']
    powers = hp['characteristics']['power_consumption']
    t_supply = hp['supply_temperature']
    load_min = hp['load_limits']['min']
    load_max = hp['load_limits']['max']
    
    return (*powers, t_supply, load_min, load_max)


def get_pump_characteristics(config_file: str = "equipment_config.json") -> float:
    """
    ④冷水ポンプ特性データ読み取り：定格動力を返す
    
    消費電力は P = A × x³ で計算される（Sui側で計算）
    
    Args:
        config_file: 機器構成JSONファイルのパス
    
    Returns:
        float: A（定格動力 kW）
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['pumps']['rated_power']


def write_timeseries(
    csv_file: str = "timeseries.csv",
    timestamp: str = "",
    total_heat_load: float = None,
    total_power: float = None,
    hp1_load: float = None,
    hp1_power: float = None,
    hp2_load: float = None,
    hp2_power: float = None,
    pump1_load: float = None,
    pump1_power: float = None,
    pump2_load: float = None,
    pump2_power: float = None
) -> None:
    """
    ⑤時系列データ書き込み：計算結果を既存の行に追記する
    
    Args:
        csv_file: 時系列CSVファイルのパス
        timestamp: タイムスタンプ文字列
        total_heat_load: 要求熱負荷 (kW)
        total_power: 総消費電力 (kW)
        hp1_load: HP1負荷率 (%)
        hp1_power: HP1消費電力 (kW)
        hp2_load: HP2負荷率 (%)
        hp2_power: HP2消費電力 (kW)
        pump1_load: ポンプ1負荷率 (0-1)
        pump1_power: ポンプ1消費電力 (kW)
        pump2_load: ポンプ2負荷率 (0-1)
        pump2_power: ポンプ2消費電力 (kW)
    """
    # 既存の行を読み込み
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # 指定されたタイムスタンプの行を更新
    found = False
    for row in rows:
        if row['time'] == timestamp:
            if total_heat_load is not None:
                row['total_heat_load'] = total_heat_load
            if total_power is not None:
                row['total_power'] = total_power
            if hp1_load is not None:
                row['hp1_load'] = hp1_load
            if hp1_power is not None:
                row['hp1_power'] = hp1_power
            if hp2_load is not None:
                row['hp2_load'] = hp2_load
            if hp2_power is not None:
                row['hp2_power'] = hp2_power
            if pump1_load is not None:
                row['pump1_load'] = pump1_load
            if pump1_power is not None:
                row['pump1_power'] = pump1_power
            if pump2_load is not None:
                row['pump2_load'] = pump2_load
            if pump2_power is not None:
                row['pump2_power'] = pump2_power
            found = True
            break
    
    if not found:
        raise ValueError(f"Timestamp {timestamp} not found in {csv_file}")
    
    # ファイルに書き込み
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# テスト用のメイン関数
if __name__ == "__main__":
    print("=== Testing Utility Functions ===")
    
    # ①機器台数取得
    count = get_equipment_count()
    print(f"Equipment count: {count}")
    
    # ②時系列データ読み取り
    t2, F2 = read_timeseries("timeseries.csv", "202512071900")
    print(f"Timeseries data: t2={t2}°C, F2={F2}L/min")
    
    # ③HP特性取得
    hp_chars = get_hp_characteristics()
    print(f"HP characteristics: {hp_chars}")
    
    # ④ポンプ特性取得
    pump_power = get_pump_characteristics()
    print(f"Pump rated power: {pump_power}kW")
    
    # ⑤書き込みテスト
    write_timeseries(
        "timeseries.csv",
        "202512071900",
        total_power=45.2,
        hp1_load=80.0,
        hp1_power=25.0,
        hp2_load=60.0,
        hp2_power=18.0,
        pump1_load=0.75,
        pump1_power=1.5,
        pump2_load=0.56,
        pump2_power=0.7
    )
    print("Output written successfully!")
