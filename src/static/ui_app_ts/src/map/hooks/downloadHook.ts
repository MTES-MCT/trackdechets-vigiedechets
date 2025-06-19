import { useState } from "react";
import axios, { AxiosResponse } from "axios";

/**
 * Custom hook for downloading files from API endpoints, get and post
 */
export const useFileDownload = () => {
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const getCsrfToken = (): string => {
    const name = "csrftoken";
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      const partValue = parts.pop();
      return partValue ? partValue.split(";").shift() || "" : "";
    }
    return "";
  };

  const processDownload = (
    response: AxiosResponse<Blob>,
    defaultFilename = "download",
  ): void => {
    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers["content-disposition"];
    let filename = defaultFilename;

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch.length === 2) {
        filename = filenameMatch[1];
      }
    }

    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);

    // Create temporary link element and trigger download
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();

    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
  };

  const extractErrorMessageFromBlob = async (blob: Blob): Promise<string> => {
    try {
      const text = await blob.text();

      // Try to parse the text as JSON
      try {
        const jsonError = JSON.parse(text);
        return jsonError.detail || jsonError.error || text;
      } catch (e) {
        // If it's not JSON, return the text as is (it might be a plain text error)
        return text;
      }
    } catch (e) {
      return "Failed to parse error message";
    }
  };

  const getErrorMessage = async (error: unknown): Promise<string> => {
    if (axios.isAxiosError(error)) {
      const response = error.response;

      // If we have a response with data that's a Blob (because we asked for responseType: 'blob')
      if (response?.data instanceof Blob) {
        // Check if this is actually a JSON error response
        const contentType = response.headers["content-type"];
        if (contentType && contentType.includes("application/json")) {
          return await extractErrorMessageFromBlob(response.data);
        }

        // If it's text/plain or we're not sure, try to read it anyway
        if (response.data.size > 0) {
          return await extractErrorMessageFromBlob(response.data);
        }
      }

      // Standard error handling for non-blob responses
      if (response?.data) {
        if (typeof response.data === "string") {
          return response.data;
        }
        return (
          response.data.detail ||
          response.data.error ||
          error.message ||
          "Unknown error"
        );
      }

      return error.message || "Request failed";
    }

    if (error instanceof Error) {
      return error.message;
    }

    return "An unknown error occurred";
  };

  const downloadWithGet = async (
    url: string,
    params: Record<string, any> = {},
    defaultFilename = "download.csv",
  ): Promise<boolean> => {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      const response = await axios<Blob>({
        url,
        method: "GET",
        params,
        responseType: "blob",
        withCredentials: true,
      });

      // Check if we might have received an error response in JSON format
      const contentType = response.headers["content-type"];
      if (contentType && contentType.includes("application/json")) {
        const errorMessage = await extractErrorMessageFromBlob(response.data);
        setDownloadError(errorMessage);
        return false;
      }

      processDownload(response, defaultFilename);
      return true;
    } catch (error: unknown) {
      console.error("Download failed:", error);
      const errorMessage = await getErrorMessage(error);
      setDownloadError(errorMessage);
      return false;
    } finally {
      setIsDownloading(false);
    }
  };

  const downloadWithPost = async (
    url: string,
    data: Record<string, any> = {},
    defaultFilename = "download.csv",
  ): Promise<boolean> => {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      const response = await axios<Blob>({
        url,
        method: "POST",
        data,
        responseType: "blob",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        withCredentials: true,
      });

      // Check if we might have received an error response in JSON format
      const contentType = response.headers["content-type"];
      if (contentType && contentType.includes("application/json")) {
        const errorMessage = await extractErrorMessageFromBlob(response.data);
        setDownloadError(errorMessage);
        return false;
      }

      processDownload(response, defaultFilename);
      return true;
    } catch (error: unknown) {
      console.error("Download failed:", error);
      const errorMessage = await getErrorMessage(error);
      setDownloadError(errorMessage);
      return false;
    } finally {
      setIsDownloading(false);
    }
  };

  return {
    downloadWithGet,
    downloadWithPost,
    isDownloading,
    downloadError,
  };
};
