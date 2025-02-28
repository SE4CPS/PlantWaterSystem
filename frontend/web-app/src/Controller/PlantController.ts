// import authService from "../Services/AuthServices";
import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";
import { toast } from "react-toastify";
import { responseErrorObject } from "../Utils/global";

// Dummy AuthController
class PlantController{
    public getPlants= async (): Promise<AxiosResponse> =>{
        try{
            const response = await axiosInstance.get('/plant/data');
            return response.data;
            // eslint-disable-next-line
        }catch(error: any){
            if(error instanceof Error){
                toast.error(error.message, {
                    position: "top-right",
                })
            }
            return {
                ...responseErrorObject,
                status: error.code,
                statusText: error.message
            } as AxiosResponse
        }
    }
}

const plantController = new PlantController();

export default plantController;