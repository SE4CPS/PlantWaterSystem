import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";
import { LoginObject } from "../Interfaces/AuthInterfaces";

class AuthController{

    public login = async (body: LoginObject): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.post('/token', body);
            return response;
        } catch (error: unknown) {
            return Promise.reject(error);
        }
    }
    
}

const authController = new AuthController();

export default authController;

