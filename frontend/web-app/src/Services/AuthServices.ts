// This is an example of how to create service 
// please remember that I have used any as an interface for some variable 
// but that is not good please make specific interface for specific variable used in controller and service.

import { UserData } from "../Interfaces/AuthInterfaces";


class AuthService{
    public getUsers=(data:Array<UserData>)=>{
        return data.map((userData: UserData)=>{
            return {
                name: userData.username
            }
        })
    }
}

const authService = new AuthService();

export default authService;