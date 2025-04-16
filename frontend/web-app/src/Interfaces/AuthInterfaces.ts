// Dummy AuthInterfaces

export interface AuthContextState{
    authUser: string,
    authToken: string,
    isLoading: boolean,
}

export interface AuthContextAction{
    type: string,
    data: {
        authUser: string,
        authToken: string,
    }
}


// Login Interfaces

export interface LoginObject{
    username: string;
    userpassword: string;
}

export interface UserSettings{
    email:string;
    firstname:string;
    lastname:string;
    phonenumber:string;
    username:string;
}

export interface UserDetails extends UserSettings{
    userid: number;
    deviceid: string;
}