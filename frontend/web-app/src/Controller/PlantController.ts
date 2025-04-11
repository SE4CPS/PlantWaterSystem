import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";
import { AddPlantRequestBody } from "../Interfaces/plantInterface";

class PlantController{
    public getPlants= async (): Promise<AxiosResponse> =>{
        try{
            const userobject = localStorage.getItem('userDetails');
            const user = userobject ? JSON.parse(userobject) : {};
            const response = await axiosInstance.get(`/sensor_data/user/${user.username || ''}`);
            return response.data;
        }catch(error: unknown){
            return Promise.reject(error)
        }
    }

    public getPlantStatus = async (sensorid: string, deviceid: string): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.get(`/plant/moisture_level?sensorid=${sensorid}&deviceid=${deviceid}`);
            return response;
        } catch (error: unknown) {
            return Promise.reject(error);
        }
    }

    public deletePlant = async (sensorid: string): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.delete(`/sensor/${sensorid}`);
            return response;
        } catch (error) {
            return Promise.reject(error);
        }
    }

    public addPlant = async (body: AddPlantRequestBody): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.post('/plant/data', body);
            return response;
        } catch (error) {
            return Promise.reject(error);
        }
    }
}

const plantController = new PlantController();

export default plantController;

