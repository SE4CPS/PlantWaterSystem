import { AxiosResponse } from "axios";
import axiosInstance from "../Utils/axiosInstance";

class SensorController{
    public getSensorData = async (deviceID: string, sensorID: string): Promise<AxiosResponse> => {
        try {
            const response = await axiosInstance.get(`/sensor_data_details?deviceid=${deviceID}&sensorid=${sensorID}`);
            return response;
        } catch (error) {
            return Promise.reject(error);
        }
    }
}

const sensorController = new SensorController();

export default sensorController;

