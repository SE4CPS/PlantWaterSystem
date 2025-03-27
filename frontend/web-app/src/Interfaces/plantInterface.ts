export interface GetPlantData{
    PlantID: number;
    PlantName: string;
    ScientificName: string;
    Threshhold: number;
}

export interface AddPlantObject{
    name: string;
    sensorId: string;
    note: string;
}