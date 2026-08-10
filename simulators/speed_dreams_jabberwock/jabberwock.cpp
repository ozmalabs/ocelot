/*
 * Speed Dreams robot module: deterministic simulator I/O only.
 *
 * This module publishes raw car/track/race telemetry over localhost UDP and
 * applies the most recent graph-authored actuator packet.  It contains no
 * racing line, target speed, steering controller, opponent policy, recovery,
 * learning, or damage logic.
 */
#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <car.h>
#include <raceman.h>
#include <robot.h>
#include <robottools.h>
#include <tgf.h>
#include <track.h>

namespace {

constexpr std::uint32_t kTelemetryMagic = 0x4a57544d;  // "JWTM"
constexpr std::uint32_t kCommandMagic = 0x4a57434d;    // "JWCM"
constexpr std::uint16_t kProtocolVersion = 2;
constexpr std::uint16_t kDefaultCommandPort = 31001;
constexpr std::uint16_t kDefaultTelemetryPort = 31002;
constexpr unsigned int kRobotInterfaceCount = 1;
constexpr int kCommandWaitMilliseconds = 25;
constexpr double kNearHorizonM = 18.0;
constexpr double kMiddleHorizonM = 55.0;
constexpr double kFarHorizonM = 110.0;
constexpr double kAnglePi = 3.14159265358979323846;
constexpr double kKelvinOffset = 273.15;

#pragma pack(push, 1)
struct TelemetryPacket {
    std::uint32_t magic;
    std::uint16_t version;
    std::uint16_t byte_count;
    std::uint64_t sequence;
    double simulation_time_s;
    double delta_time_s;
    double speed_m_s;
    double body_vx_m_s;
    double body_vy_m_s;
    double yaw_rate_rad_s;
    double slip_angle_rad;
    double longitudinal_accel_m_s2;
    double lateral_accel_m_s2;
    double track_progress_m;
    double track_length_m;
    double track_lateral_m;
    double track_half_width_m;
    double heading_error_rad;
    double curvature_now_inv_m;
    double curvature_near_inv_m;
    double curvature_middle_inv_m;
    double curvature_far_inv_m;
    double curvature_envelope_near_inv_m;
    double curvature_envelope_middle_inv_m;
    double curvature_envelope_far_inv_m;
    double surface_grip;
    double front_slip_rad;
    double rear_slip_rad;
    double front_normal_load_n;
    double rear_normal_load_n;
    double tyre_temperature_mean_c;
    double tyre_condition_mean;
    double brake_temperature_mean;
    double fuel_l;
    double damage;
    double nearest_opponent_ahead_m;
    double nearest_opponent_lateral_m;
    double nearest_opponent_speed_m_s;
    double nearest_opponent_closing_m_s;
    double engine_rpm;
    std::int32_t gear;
    std::int32_t laps;
    std::int32_t race_position;
    std::int32_t collision_count;
    std::int32_t pit_stops;
    std::int32_t total_laps;
};

struct CommandPacket {
    std::uint32_t magic;
    std::uint16_t version;
    std::uint16_t byte_count;
    std::uint64_t telemetry_sequence;
    double steering;
    double throttle;
    double brake;
    double clutch;
    double front_wing;
    double rear_wing;
    double drive_front_left;
    double drive_front_right;
    double drive_rear_left;
    double drive_rear_right;
    double brake_front_left;
    double brake_front_right;
    double brake_rear_left;
    double brake_rear_right;
    std::int32_t gear;
    std::int32_t pit_request;
};
#pragma pack(pop)

static_assert(sizeof(TelemetryPacket) == 328);
static_assert(sizeof(CommandPacket) == 136);

int g_socket = -1;
sockaddr_in g_telemetry_address{};
std::uint64_t g_sequence = 0;
CommandPacket g_command{};
bool g_has_command = false;
double g_track_length_m = 0.0;

double clamp_value(double value, double lower, double upper) {
    return std::max(lower, std::min(upper, value));
}

double wrap_angle(double angle) {
    while (angle > kAnglePi) {
        angle -= 2.0 * kAnglePi;
    }
    while (angle < -kAnglePi) {
        angle += 2.0 * kAnglePi;
    }
    return angle;
}

std::uint16_t environment_port(const char* name, std::uint16_t fallback) {
    const char* text = std::getenv(name);
    if (text == nullptr || *text == '\0') {
        return fallback;
    }
    const long parsed = std::strtol(text, nullptr, 10);
    if (parsed < 1 || parsed > 65535) {
        return fallback;
    }
    return static_cast<std::uint16_t>(parsed);
}

double segment_curvature(const tTrackSeg* segment) {
    if (segment == nullptr || segment->type == TR_STR || segment->radius <= 0.0) {
        return 0.0;
    }
    const double magnitude = 1.0 / segment->radius;
    return segment->type == TR_LFT ? magnitude : -magnitude;
}

struct CurvatureScan {
    double point_near = 0.0;
    double point_middle = 0.0;
    double point_far = 0.0;
    double envelope_near = 0.0;
    double envelope_middle = 0.0;
    double envelope_far = 0.0;
};

CurvatureScan scan_curvature(const tTrackSeg* start) {
    CurvatureScan scan;
    if (start == nullptr) {
        return scan;
    }
    const tTrackSeg* segment = start;
    double distance = 0.0;
    bool near_written = false;
    bool middle_written = false;
    bool far_written = false;
    do {
        const double curvature = segment_curvature(segment);
        const double magnitude = std::abs(curvature);
        if (distance <= kNearHorizonM) {
            scan.envelope_near = std::max(scan.envelope_near, magnitude);
        } else if (distance <= kMiddleHorizonM) {
            scan.envelope_middle = std::max(scan.envelope_middle, magnitude);
        } else if (distance <= kFarHorizonM) {
            scan.envelope_far = std::max(scan.envelope_far, magnitude);
        }
        if (!near_written && distance >= kNearHorizonM) {
            scan.point_near = curvature;
            near_written = true;
        }
        if (!middle_written && distance >= kMiddleHorizonM) {
            scan.point_middle = curvature;
            middle_written = true;
        }
        if (!far_written && distance >= kFarHorizonM) {
            scan.point_far = curvature;
            far_written = true;
        }
        distance += std::max(0.0, static_cast<double>(segment->length));
        segment = segment->next;
    } while (segment != nullptr && segment != start && distance <= kFarHorizonM);
    return scan;
}

void open_bridge_socket() {
    if (g_socket >= 0) {
        return;
    }
    g_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (g_socket < 0) {
        return;
    }
    const int flags = fcntl(g_socket, F_GETFL, 0);
    fcntl(g_socket, F_SETFL, flags | O_NONBLOCK);
    sockaddr_in command_address{};
    command_address.sin_family = AF_INET;
    command_address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    command_address.sin_port = htons(environment_port(
        "JABBERWOCK_SD_COMMAND_PORT",
        kDefaultCommandPort
    ));
    if (bind(
            g_socket,
            reinterpret_cast<const sockaddr*>(&command_address),
            sizeof(command_address)
        ) != 0) {
        close(g_socket);
        g_socket = -1;
        return;
    }
    g_telemetry_address.sin_family = AF_INET;
    g_telemetry_address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    g_telemetry_address.sin_port = htons(environment_port(
        "JABBERWOCK_SD_TELEMETRY_PORT",
        kDefaultTelemetryPort
    ));
}

void receive_latest_command(std::uint64_t requested_sequence) {
    if (g_socket < 0) {
        return;
    }
    pollfd descriptor{g_socket, POLLIN, 0};
    if (poll(&descriptor, 1, kCommandWaitMilliseconds) > 0) {
        CommandPacket candidate{};
        while (recv(
            g_socket,
            &candidate,
            sizeof(candidate),
            0
        ) == static_cast<ssize_t>(sizeof(candidate))) {
            if (
                candidate.magic == kCommandMagic
                && candidate.version == kProtocolVersion
                && candidate.byte_count == sizeof(CommandPacket)
                && candidate.telemetry_sequence <= g_sequence
            ) {
                g_command = candidate;
                g_has_command = true;
                if (candidate.telemetry_sequence >= requested_sequence) {
                    break;
                }
            }
        }
    }
}

void nearest_opponent(
    const tCarElt* car,
    const tSituation* situation,
    double* gap_m,
    double* lateral_m,
    double* speed_m_s
) {
    *gap_m = g_track_length_m;
    *lateral_m = 0.0;
    *speed_m_s = car->_speed_x;
    for (int index = 0; index < situation->_ncars; ++index) {
        const tCarElt* other = situation->cars[index];
        if (other == nullptr || other == car || (other->_state & RM_CAR_STATE_OUT)) {
            continue;
        }
        double gap = other->_distRaced - car->_distRaced;
        while (gap < 0.0) {
            gap += g_track_length_m;
        }
        if (gap < *gap_m) {
            *gap_m = gap;
            *lateral_m = other->_trkPos.toMiddle - car->_trkPos.toMiddle;
            *speed_m_s = other->_speed_x;
        }
    }
}

TelemetryPacket make_telemetry(const tCarElt* car, const tSituation* situation) {
    TelemetryPacket packet{};
    packet.magic = kTelemetryMagic;
    packet.version = kProtocolVersion;
    packet.byte_count = sizeof(TelemetryPacket);
    packet.sequence = ++g_sequence;
    packet.simulation_time_s = situation->currentTime;
    packet.delta_time_s = situation->deltaTime;
    packet.speed_m_s = car->_speed_xy;
    packet.body_vx_m_s = car->_speed_x;
    packet.body_vy_m_s = car->_speed_y;
    packet.yaw_rate_rad_s = car->_yaw_rate;
    packet.slip_angle_rad = std::atan2(
        static_cast<double>(car->_speed_y),
        std::max(0.001, std::abs(static_cast<double>(car->_speed_x)))
    );
    packet.longitudinal_accel_m_s2 = car->_accel_x;
    packet.lateral_accel_m_s2 = car->_accel_y;
    packet.track_progress_m = car->_distFromStartLine;
    packet.track_length_m = g_track_length_m;
    packet.track_lateral_m = car->_trkPos.toMiddle;
    packet.track_half_width_m = car->_trkPos.seg == nullptr
        ? 0.0
        : car->_trkPos.seg->width * 0.5;
    packet.heading_error_rad = wrap_angle(
        RtTrackSideTgAngleL(const_cast<tTrkLocPos*>(&car->_trkPos)) - car->_yaw
    );
    packet.curvature_now_inv_m = segment_curvature(car->_trkPos.seg);
    const CurvatureScan scan = scan_curvature(car->_trkPos.seg);
    packet.curvature_near_inv_m = scan.point_near;
    packet.curvature_middle_inv_m = scan.point_middle;
    packet.curvature_far_inv_m = scan.point_far;
    packet.curvature_envelope_near_inv_m = scan.envelope_near;
    packet.curvature_envelope_middle_inv_m = scan.envelope_middle;
    packet.curvature_envelope_far_inv_m = scan.envelope_far;
    packet.surface_grip = (
        car->_trkPos.seg != nullptr && car->_trkPos.seg->surface != nullptr
    ) ? car->_trkPos.seg->surface->kFriction : 1.0;
    packet.front_slip_rad = 0.5 * (
        car->_wheelSlipSide(FRNT_LFT) + car->_wheelSlipSide(FRNT_RGT)
    );
    packet.rear_slip_rad = 0.5 * (
        car->_wheelSlipSide(REAR_LFT) + car->_wheelSlipSide(REAR_RGT)
    );
    packet.front_normal_load_n = (
        car->_wheelFz(FRNT_LFT) + car->_wheelFz(FRNT_RGT)
    );
    packet.rear_normal_load_n = (
        car->_wheelFz(REAR_LFT) + car->_wheelFz(REAR_RGT)
    );
    for (int wheel = 0; wheel < 4; ++wheel) {
        packet.tyre_temperature_mean_c += (
            car->_tyreT_in(wheel) - kKelvinOffset
            + car->_tyreT_mid(wheel) - kKelvinOffset
            + car->_tyreT_out(wheel) - kKelvinOffset
        ) / 12.0;
        packet.tyre_condition_mean += car->_tyreTreadDepth(wheel) * 0.25;
        packet.brake_temperature_mean += car->_brakeTemp(wheel) * 0.25;
    }
    packet.fuel_l = car->_fuel;
    packet.damage = car->_dammage;
    double opponent_speed = car->_speed_x;
    nearest_opponent(
        car,
        situation,
        &packet.nearest_opponent_ahead_m,
        &packet.nearest_opponent_lateral_m,
        &opponent_speed
    );
    packet.nearest_opponent_speed_m_s = opponent_speed;
    packet.nearest_opponent_closing_m_s = car->_speed_x - opponent_speed;
    packet.engine_rpm = car->_enginerpm;
    packet.gear = car->_gear;
    packet.laps = car->_laps;
    packet.race_position = car->_pos;
    packet.collision_count = car->_collCount;
    packet.pit_stops = car->_nbPitStops;
    packet.total_laps = situation->_totLaps;
    return packet;
}

void drive(int, tCarElt* car, tSituation* situation) {
    open_bridge_socket();
    const TelemetryPacket telemetry = make_telemetry(car, situation);
    if (g_socket >= 0) {
        sendto(
            g_socket,
            &telemetry,
            sizeof(telemetry),
            0,
            reinterpret_cast<const sockaddr*>(&g_telemetry_address),
            sizeof(g_telemetry_address)
        );
    }
    receive_latest_command(telemetry.sequence);
    if (!g_has_command) {
        car->_steerCmd = 0.0;
        car->_accelCmd = 0.0;
        car->_brakeCmd = 1.0;
        car->_singleWheelBrakeMode = 0;
        car->_clutchCmd = 0.0;
        car->_gearCmd = std::max(1, car->_gear);
        return;
    }
    car->_steerCmd = clamp_value(g_command.steering, -1.0, 1.0);
    car->_accelCmd = clamp_value(g_command.throttle, 0.0, 1.0);
    // The 2.4.2 robot ABI exposes four brake channels but only one engine
    // accelerator. Preserve the graph's individual brake commands exactly;
    // the aggregate accelerator remains the honest limit of this backend.
    car->_brakeCmd = 0.0;
    car->_singleWheelBrakeMode = 1;
    const double front_brake_fraction = clamp_value(
        car->setup.brakeRepartition.value,
        0.0,
        1.0
    );
    const double rear_brake_fraction = 1.0 - front_brake_fraction;
    car->_brakeFLCmd = front_brake_fraction
        * clamp_value(g_command.brake_front_left, 0.0, 1.0);
    car->_brakeFRCmd = front_brake_fraction
        * clamp_value(g_command.brake_front_right, 0.0, 1.0);
    car->_brakeRLCmd = rear_brake_fraction
        * clamp_value(g_command.brake_rear_left, 0.0, 1.0);
    car->_brakeRRCmd = rear_brake_fraction
        * clamp_value(g_command.brake_rear_right, 0.0, 1.0);
    car->_clutchCmd = clamp_value(g_command.clutch, 0.0, 1.0);
    car->_wingFCmd = clamp_value(g_command.front_wing, 0.0, 1.0);
    car->_wingRCmd = clamp_value(g_command.rear_wing, 0.0, 1.0);
    car->_gearCmd = std::max(1, std::min(car->_gearNb - 1, g_command.gear));
    car->_raceCmd = g_command.pit_request ? RM_CMD_PIT_ASKED : 0;
}

void new_track(int, tTrack* track, void*, void**, tSituation*) {
    g_track_length_m = track == nullptr ? 0.0 : track->length;
}

void new_race(int, tCarElt*, tSituation*) {
    g_sequence = 0;
    g_has_command = false;
    open_bridge_socket();
}

int pit_command(int, tCarElt*, tSituation*) {
    return ROB_PIT_IM;
}

void end_race(int, tCarElt*, tSituation*) {}

void shutdown(int) {
    if (g_socket >= 0) {
        close(g_socket);
        g_socket = -1;
    }
    g_has_command = false;
}

int initialize_interface(int index, void* interface_pointer) {
    auto* interface = static_cast<tRobotItf*>(interface_pointer);
    interface->rbNewTrack = new_track;
    interface->rbNewRace = new_race;
    interface->rbDrive = drive;
    interface->rbPitCmd = pit_command;
    interface->rbEndRace = end_race;
    interface->rbShutdown = shutdown;
    interface->index = index;
    return 0;
}

}  // namespace

int initialize_module(tModInfo* module_info) {
    std::memset(module_info, 0, sizeof(tModInfo));
    module_info[0].name = "Jabberwock";
    module_info[0].desc = "Policy-free UDP bridge to graph-native cognition";
    module_info[0].fctInit = initialize_interface;
    module_info[0].gfId = ROB_IDENT;
    module_info[0].index = 0;
    return 0;
}

extern "C" int moduleWelcome(
    const tModWelcomeIn*,
    tModWelcomeOut* welcome
) {
    welcome->maxNbItf = kRobotInterfaceCount;
    return 0;
}

extern "C" int moduleInitialize(tModInfo* module_info) {
    return initialize_module(module_info);
}

extern "C" int moduleTerminate() {
    shutdown(0);
    return 0;
}

// Speed Dreams still probes the legacy, module-named entry points when
// inspecting older robot packages. Keep them as exact ABI aliases.
extern "C" int jabberwock(tModInfo* module_info) {
    return initialize_module(module_info);
}

extern "C" int jabberwockShut() {
    return moduleTerminate();
}
