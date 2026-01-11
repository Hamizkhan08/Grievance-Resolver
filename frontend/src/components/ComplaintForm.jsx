import React, { useState } from "react";
import axios from "axios";
import { Loader2, Send } from "lucide-react";
import { useTranslation } from "../hooks/useTranslation";
import VoiceInput from "./VoiceInput";
import "./ComplaintForm.css";
import { API_URL as API_BASE_URL } from "../lib/config";

const ComplaintForm = ({ onSuccess }) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    description: "",
    citizen_name: "",
    citizen_email: "",
    citizen_phone: "",
    location: {
      country: "India",
      state: "",
      city: "",
      district: "",
      pincode: "",
      address: "",
    },
  });

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith("location.")) {
      const locationField = name.split(".")[1];
      setFormData((prev) => ({
        ...prev,
        location: {
          ...prev.location,
          [locationField]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setFormData((prev) => ({
      ...prev,
      location: {
        ...prev.location,
        state: location.state || prev.location.state,
        city: location.city || prev.location.city,
        district: location.district || prev.location.district,
        pincode: location.pincode || prev.location.pincode,
        address: location.address || prev.location.address,
      },
    }));
  };

  const handleVoiceTranscript = (transcript) => {
    setFormData((prev) => ({
      ...prev,
      description: prev.description
        ? prev.description + " " + transcript
        : transcript,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/complaints`, {
        description: formData.description,
        citizen_name: formData.citizen_name,
        citizen_email: formData.citizen_email,
        citizen_phone: formData.citizen_phone,
        location: formData.location,
        attachments: [],
      });

      if (response.data.success) {
        onSuccess(response.data.complaint);
      } else {
        setError(response.data.error || t("formError"));
      }
    } catch (err) {
      setError(
        err.response?.data?.error || err.message || t("formErrorGeneric")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="complaint-form">
      <div className="form-group">
        <label htmlFor="citizen_name">{t("formYourName")}</label>
        <div className="input-wrapper">
          <input
            type="text"
            id="citizen_name"
            name="citizen_name"
            value={formData.citizen_name}
            onChange={handleInputChange}
            required
            placeholder={t("formNamePlaceholder")}
          />
          <VoiceInput
            onTranscript={(transcript) => {
              setFormData((prev) => ({
                ...prev,
                citizen_name: transcript,
              }));
            }}
            disabled={loading}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="citizen_email">{t("formEmail")}</label>
          <input
            type="email"
            id="citizen_email"
            name="citizen_email"
            value={formData.citizen_email}
            onChange={handleInputChange}
            required
            placeholder={t("formEmailPlaceholder")}
          />
        </div>

        <div className="form-group">
          <label htmlFor="citizen_phone">{t("formPhone")}</label>
          <input
            type="tel"
            id="citizen_phone"
            name="citizen_phone"
            value={formData.citizen_phone}
            onChange={handleInputChange}
            required
            pattern="[0-9]{10}"
            placeholder={t("formPhonePlaceholder")}
            maxLength="10"
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="description">{t("formDescription")}</label>
        <div className="textarea-wrapper">
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            required
            rows="6"
            placeholder={t("formDescriptionPlaceholder")}
          />
          <VoiceInput onTranscript={handleVoiceTranscript} disabled={loading} />
        </div>
        <small className="help-text">{t("formDescriptionHelp")}</small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="state">{t("formState")}</label>
          <select
            id="state"
            name="location.state"
            value={formData.location.state}
            onChange={handleInputChange}
          >
            <option value="">{t("formStatePlaceholder")}</option>
            <option value="Andhra Pradesh">Andhra Pradesh</option>
            <option value="Assam">Assam</option>
            <option value="Bihar">Bihar</option>
            <option value="Delhi">Delhi</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Kerala">Kerala</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="West Bengal">West Bengal</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="city">{t("formCity")}</label>
          <input
            type="text"
            id="city"
            name="location.city"
            value={formData.location.city}
            onChange={handleInputChange}
            placeholder={t("formCityPlaceholder")}
          />
        </div>

        <div className="form-group">
          <label htmlFor="pincode">{t("formPincode")}</label>
          <input
            type="text"
            id="pincode"
            name="location.pincode"
            value={formData.location.pincode}
            onChange={handleInputChange}
            placeholder={t("formPincodePlaceholder")}
            pattern="[0-9]{6}"
            maxLength="6"
          />
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="spinner" />
            <span>{t("formProcessing")}</span>
          </>
        ) : (
          <>
            <Send size={18} />
            <span>{t("formSubmit")}</span>
          </>
        )}
      </button>
    </form>
  );
};

export default ComplaintForm;
