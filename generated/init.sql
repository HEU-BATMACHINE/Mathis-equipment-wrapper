-- init.sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create channel tables
CREATE TABLE IF NOT EXISTS PyrometerIR_Dryer (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D1BFanControl (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D1TFanControl (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D2BFanControl (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D2TFanControl (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D1BActRot (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D1TActRot (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D2BBActRot (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS D2TActRot (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS Dryer1_TempBottom (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS Dryer1_TempTop (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS Dryer2_TempBottom (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS Dryer2_TempTop (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS RewDiameterSensor (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS UnwDiameterSensor (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS UnwWebTension (time TIMESTAMPTZ NOT NULL, value REAL NOT NULL);

-- Convert the channel tables into hypertables
SELECT create_hypertable('PyrometerIR_Dryer', 'time');
SELECT create_hypertable('D1BFanControl', 'time');
SELECT create_hypertable('D1TFanControl', 'time');
SELECT create_hypertable('D2BFanControl', 'time');
SELECT create_hypertable('D2TFanControl', 'time');
SELECT create_hypertable('D1BActRot', 'time');
SELECT create_hypertable('D1TActRot', 'time');
SELECT create_hypertable('D2BBActRot', 'time');
SELECT create_hypertable('D2TActRot', 'time');
SELECT create_hypertable('Dryer1_TempBottom', 'time');
SELECT create_hypertable('Dryer1_TempTop', 'time');
SELECT create_hypertable('Dryer2_TempBottom', 'time');
SELECT create_hypertable('Dryer2_TempTop', 'time');
SELECT create_hypertable('RewDiameterSensor', 'time');
SELECT create_hypertable('UnwDiameterSensor', 'time');
SELECT create_hypertable('UnwWebTension', 'time');
