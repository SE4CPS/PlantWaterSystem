import React, { ReactNode } from "react";
import { createContext, useReducer } from "react";
import { AuthContextAction, AuthContextState } from "../Interfaces/AuthInterfaces";

// Dummy AuthContext

const AuthContext = createContext({});

const initialState : AuthContextState={
    authUser: '',
    authToken: '',
    isLoading: false,
}

const reducer = (state: AuthContextState, action: AuthContextAction): AuthContextState =>{
    switch(action.type){
        case 'LOGIN': {
            return {...state, authUser: action.data.authUser , authToken: action.data.authToken}
        }
        default: {
            return state;
        }
    }
}

export const AuthProvider = ({children}: {children: ReactNode}) => {
    const [{authUser, authToken, isLoading}, dispatch] = useReducer(reducer, initialState);
    const values = {
        authUser,
        authToken,
        isLoading,
        dispatch,
    }
    return <AuthContext.Provider value={values}>{children}</AuthContext.Provider>

}

export default AuthContext;