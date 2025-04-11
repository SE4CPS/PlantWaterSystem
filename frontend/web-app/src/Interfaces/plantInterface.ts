export interface GetPlantData{
    plantname: string;
    sensorid: string;
    deviceid: string;
}

export interface AddPlantObject{
    name: string;
    sensorId: string;
}

export interface PlantMetaData{
    status: string;
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

export interface AddPlantRequestBody{
    plant_name: string;
    user_id: string;
    sensor_id: string;
    device_id: string;
}
