import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";

class PlantController{
    public getPlants= async (): Promise<AxiosResponse> =>{
        try{
            const userobject = localStorage.getItem('userDetails');
            const user = JSON.parse(userobject? userobject: '');
            const response = await axiosInstance.get(`/sensor_data/user/${user.username || ''}`);
            return response.data;
        }catch(error: unknown){
            return Promise.reject(error)
        }
    }

    public getPlantStatus = async (sensorid: string, deviceid: string): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.get(`/plant/last_status?sensorid=${sensorid}&deviceid=${deviceid}`);
            return response;
        } catch (error: unknown) {
            return Promise.reject(error);
        }
    }
}

const plantController = new PlantController();

export default plantController;

