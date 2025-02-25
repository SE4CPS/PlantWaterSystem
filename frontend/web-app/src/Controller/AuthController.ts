import authService from "../Services/AuthServices";
import axiosInstance from "../Utils/axiosInstance";

// Dummy AuthController
class AuthController{
    public getUsers= async (): Promise<any> =>{
        try{
            const body={ "PlantID":50009, "PlantName": "orchids", "ScientificName": "ordcha", "Threshhold": 20.0 }
            const response = await axiosInstance.post('/plant/data', body);
            // const usersData = authService.getUsers(response.data);
            return response;
        }catch(error){
            throw new Error('Error getUsers');
        }
    }
}

const authController = new AuthController();

export default authController;