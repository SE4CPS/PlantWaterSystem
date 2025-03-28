export interface GetPlantData{
    plantname: string;
    sensorid: string;
    deviceid: string;
}

export interface AddPlantObject{
    name: string;
    sensorId: string;
    note: string;
}

export interface PlantMetaData{
    name: string;
    sensorId: string;
    deviceId: string;
}

export interface SensorTableData{
    date: string,
    time: string,
    adcvalue: string;
    moisture_level: string;
    digitalsatus: string;
}