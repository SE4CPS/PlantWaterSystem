// import authService from "../Services/AuthServices";
import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";
import { toast } from "react-toastify";
import { responseErrorObject } from "../Utils/global";

// Dummy AuthController
class AuthController{
    public getUsers= async (): Promise<AxiosResponse> =>{
        try{
            const body={ "PlantID":50009, "PlantName": "orchids", "ScientificName": "ordcha", "Threshhold": 20.0 }
            const response = await axiosInstance.post('/plant/data', body);
            // const usersData = authService.getUsers(response.data);
            return response;
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

const authController = new AuthController();

export default authController;