import axios from "axios";
import { toast } from "react-toastify";

const handleApiError = (error:unknown) => {
    if(axios.isAxiosError(error)){
        if(error.response){
            toast.error(error.response.data.message || "Something went wrong!", {
                position: "top-right",
            })
        } else if(error.request){
            toast.error("Network error! Please check your connection", {
                position: "top-right",
            })
        } else{
            toast.error("An Unexpected Error occurred", {
                position: "top-right",
            })
        }
    } else {
        toast.error("An Unknown Error occurred", {
            position: "top-right",
        })
    }
}

export default handleApiError;