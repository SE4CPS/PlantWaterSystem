import authService from "../Services/AuthServices";
import axiosInstance from "../Utils/axiosInstance";

// Dummy AuthController
class AuthController{
    public getUsers= async (): Promise<any> =>{
        try{
            const response = await axiosInstance.get('/users');
            const usersData = authService.getUsers(response.data);
            return usersData;
        }catch(error){
            throw new Error('Error getUsers');
        }
    }
}

const authController = new AuthController();

export default authController;