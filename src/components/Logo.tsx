import logo_img from "../assets/logo.png";

const Logo = () => {
  return (
    <div className="flex items-center">
      <img
        src={logo_img}
        alt="ForeSyte Logo"
        className="w-[120px] h-[120px] object-contain drop-shadow-xl"
      />
    </div>
  );
};

export default Logo;
