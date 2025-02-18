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