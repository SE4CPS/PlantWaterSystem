import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";

class PlantController{
    public getPlants= async (): Promise<AxiosResponse> =>{
        try{
            const response = await axiosInstance.get('/sensor_data/user/alice_s');
            return response.data;
        }catch(error: unknown){
            return Promise.reject(error)
        }
    }
}

const plantController = new PlantController();

export default plantController;

